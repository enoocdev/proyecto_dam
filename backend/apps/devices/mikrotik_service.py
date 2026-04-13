import logging
import ssl
from contextlib import contextmanager

from librouteros import connect

from .models import NetworkDevice, AllowedHost

logger = logging.getLogger("devices.mikrotik")

COMMENT_PREFIX = "MONITOR"
COMMENT_DEVICE_BLOCK = f"{COMMENT_PREFIX}_BLOCK"
COMMENT_GLOBAL_BLOCK = f"{COMMENT_PREFIX}_GLOBAL_BLOCK"
COMMENT_CLASSROOM_BLOCK = f"{COMMENT_PREFIX}_CLASS_BLOCK"

HORIZON_GLOBAL_BLOCK = 400_000_000
HORIZON_CLASSROOM_BASE = 410_000_000
HORIZON_DEVICE_BASE = 420_000_000
HORIZON_MAX_OFFSET = 9_000_000


class MikrotikError(Exception):
    pass


def _get_allowed_hosts():
    return list(AllowedHost.objects.values_list("ip_address", flat=True))


def _to_cidr(ip: str) -> str:
    ip_str = str(ip)
    return f"{ip_str}/32" if "/" not in ip_str else ip_str


@contextmanager
def _mikrotik_connection(network_device: NetworkDevice):
    try:
        ssl_ctx = None
        
        if network_device.api_port == 8729:
            ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
            ssl_ctx.options |= getattr(ssl, "OP_LEGACY_SERVER_CONNECT", 0x40000)
            ssl_ctx.set_ciphers('ALL:@SECLEVEL=0')
            
            logger.debug("Conexion segura TLS para %s", network_device.ip_address)
        else:
            logger.debug("Conexion plana para %s", network_device.ip_address)
            
        api = connect(
            host=str(network_device.ip_address),
            username=network_device.username,
            password=network_device.password,
            port=network_device.api_port,
            ssl_wrapper=ssl_ctx.wrap_socket if ssl_ctx else None,
            timeout=10
        )
    except Exception as exc:
        raise MikrotikError(f"Fallo al conectar con router {network_device.ip_address}: {exc}") from exc
    
    try:
        yield api
    finally:
        api.close()


def _get_bridge_filter(api):
    return api.path("/interface/bridge/filter")


def _get_ip_filter(api):
    """Accede a la tabla de reglas del firewall IP (/ip/firewall/filter)."""
    return api.path("/ip/firewall/filter")


def _build_device_comment(device_id: int) -> str:
    return f"{COMMENT_DEVICE_BLOCK}_{device_id}"


def _remove_rules_by_comment(api, comment: str):
    """Elimina reglas con el comentario dado de bridge filter Y de IP firewall filter."""
    # Limpiar bridge filter
    filt = _get_bridge_filter(api)
    rules_to_remove = [rule[".id"] for rule in filt if rule.get("comment", "") == comment]
    for rule_id in reversed(rules_to_remove):
        filt.remove(rule_id)
        logger.info("Regla bridge eliminada: id=%s comment=%s", rule_id, comment)

    # Limpiar IP firewall filter
    ip_filt = _get_ip_filter(api)
    ip_rules_to_remove = [rule[".id"] for rule in ip_filt if rule.get("comment", "") == comment]
    for rule_id in reversed(ip_rules_to_remove):
        ip_filt.remove(rule_id)
        logger.info("Regla IP firewall eliminada: id=%s comment=%s", rule_id, comment)


def _get_first_chain_rule_id(path, chain: str):
    """Busca el .id de la primera regla existente en la cadena indicada."""
    rule = next((r for r in path if r.get("chain") == chain), None)
    return rule[".id"] if rule else None


def _add_rules_with_placement(path, rules: list, chain: str):
    """Anade reglas a un path de MikroTik colocandolas antes de la primera regla
    existente de la cadena indicada para que tengan prioridad."""
    first_id = _get_first_chain_rule_id(path, chain)
    for rule_params in rules:
        if first_id:
            rule_params["place-before"] = first_id
        path.add(**rule_params)


#  Helpers para horizon y bridge use-ip-firewall

def _device_horizon(device_id: int) -> int:
    return HORIZON_DEVICE_BASE


def _classroom_horizon(classroom_id: int) -> int:
    return HORIZON_CLASSROOM_BASE + (int(classroom_id) % HORIZON_MAX_OFFSET)


def _set_port_horizon(api, port_name: str, horizon: int | None):
    """Aplica split horizon a un puerto del bridge (/interface/bridge/port).
    - horizon=numero: bloquea forwarding hacia puertos con mismo horizon.
    - horizon=None: restaura a 'none'."""
    bridge_ports = api.path("/interface/bridge/port")
    horizon_value = "none" if horizon is None else str(horizon)

    for port in bridge_ports:
        if port.get("interface") == port_name:
            try:
                bridge_ports.update(**{".id": port[".id"], "horizon": horizon_value})
                logger.info("Horizon %s aplicado en puerto %s", horizon_value, port_name)
            except Exception as e:
                logger.warning("No se pudo cambiar horizon en %s: %s", port_name, e)
            return

    logger.debug("Puerto %s no encontrado en bridge ports", port_name)


def _set_all_ports_horizon(api, horizon: int | None):
    """Aplica horizon a todos los puertos del bridge."""
    bridge_ports = api.path("/interface/bridge/port")
    horizon_value = "none" if horizon is None else str(horizon)
    entries = [(p[".id"], p.get("interface", "?")) for p in bridge_ports]
    for pid, iface in entries:
        try:
            bridge_ports.update(**{".id": pid, "horizon": horizon_value})
        except Exception as e:
            logger.warning("No se pudo cambiar horizon en %s: %s", iface, e)


def _ensure_bridge_use_ip_firewall(api):
    """Activa use-ip-firewall en /interface/bridge/settings (configuracion GLOBAL).
    Esto hace que el trafico bridgeado pase por /ip/firewall/filter (L3).
    IMPORTANTE: use-ip-firewall NO es una propiedad per-bridge, sino un ajuste
    global en /interface/bridge/settings (Sub-menu de MikroTik)."""
    try:
        settings = api.path("/interface/bridge/settings")
        # /interface/bridge/settings es un recurso singleton (una sola entrada)
        entry = next(iter(settings), None)
        if entry is None:
            logger.warning("No se encontro entrada en /interface/bridge/settings")
            return

        if entry.get("use-ip-firewall") == "true":
            logger.debug("use-ip-firewall ya estaba activado")
            return

        settings.update(**{".id": entry[".id"], "use-ip-firewall": "yes"})
        logger.info("use-ip-firewall activado en /interface/bridge/settings")
    except Exception as e:
        logger.warning("No se pudo activar use-ip-firewall: %s", e)


def _disable_bridge_use_ip_firewall_if_clean(api):
    """Desactiva use-ip-firewall si ya no quedan reglas MONITOR_ en bridge filter
    ni en IP firewall, para restaurar el rendimiento normal del bridge."""
    # Comprobar si quedan reglas activas de monitor
    filt = _get_bridge_filter(api)
    has_bridge_rules = any(
        rule.get("comment", "").startswith(COMMENT_PREFIX) for rule in filt
    )
    if has_bridge_rules:
        return

    ip_filt = _get_ip_filter(api)
    has_ip_rules = any(
        rule.get("comment", "").startswith(COMMENT_PREFIX) for rule in ip_filt
    )
    if has_ip_rules:
        return

    try:
        settings = api.path("/interface/bridge/settings")
        entry = next(iter(settings), None)
        if entry and entry.get("use-ip-firewall") != "false":
            settings.update(**{".id": entry[".id"], "use-ip-firewall": "no"})
            logger.info("use-ip-firewall desactivado (sin reglas activas)")
    except Exception as e:
        logger.warning("No se pudo desactivar use-ip-firewall: %s", e)


#  Bloqueo / desbloqueo de un dispositivo individual

def block_device_internet(network_device, switch_port, device_id, device_ip):

    comment = _build_device_comment(device_id)
    allowed_hosts = _get_allowed_hosts()

    with _mikrotik_connection(network_device) as api:
        _remove_rules_by_comment(api, comment)

        # Horizon en el puerto del dispositivo (en lugar de bridge filter por interfaz).
        # Split-horizon es una funcion software y desactiva HW offload en ese puerto.
        _set_port_horizon(api, switch_port, _device_horizon(device_id))
        _ensure_bridge_use_ip_firewall(api)

        # =====================================================================
        #  CAPA 1  –  Horizon por puerto (L2)
        #  CAPA 2  –  IP Firewall Filter (L3, por direccion IP)
        # =====================================================================
        ip_filt = _get_ip_filter(api)
        ip_rules = []
        dev_cidr = _to_cidr(device_ip)

        # Permitir trafico IP hacia/desde cada allowed host
        for allowed_ip in allowed_hosts:
            ah_cidr = _to_cidr(allowed_ip)
            ip_rules.append({
                "chain": "forward", "action": "accept",
                "src-address": dev_cidr, "dst-address": ah_cidr,
                "comment": comment,
            })
            ip_rules.append({
                "chain": "forward", "action": "accept",
                "src-address": ah_cidr, "dst-address": dev_cidr,
                "comment": comment,
            })

        # DROP de todo lo demas desde/hacia la IP del dispositivo
        ip_rules.append({
            "chain": "forward", "action": "drop",
            "src-address": dev_cidr, "comment": comment,
        })
        ip_rules.append({
            "chain": "forward", "action": "drop",
            "dst-address": dev_cidr, "comment": comment,
        })

        _add_rules_with_placement(ip_filt, ip_rules, "forward")

    logger.info(
        "Internet bloqueado (L2+L3) para device_id=%s puerto=%s ip=%s",
        device_id, switch_port, device_ip,
    )


def unblock_device_internet(network_device, device_id):
    """Desbloquea internet eliminando reglas IP y restaurando horizon del puerto."""
    from .models import Device
    comment = _build_device_comment(device_id)

    # Obtener puerto para restaurar horizon
    try:
        device = Device.objects.get(id=device_id)
        switch_port = device.switch_port.strip() if device.switch_port else ""
    except Device.DoesNotExist:
        switch_port = ""

    with _mikrotik_connection(network_device) as api:
        _remove_rules_by_comment(api, comment)
        # Restaurar horizon del puerto
        if switch_port:
            _set_port_horizon(api, switch_port, None)
        # Desactivar use-ip-firewall si ya no quedan reglas activas
        _disable_bridge_use_ip_firewall_if_clean(api)
    logger.info("Internet desbloqueado para device_id=%s", device_id)


# ---------------------------------------------------------------------------
#  Bloqueo / desbloqueo global por equipo de red
# ---------------------------------------------------------------------------

def global_block_internet(network_device):
    """Bloquea todo el trafico IP excepto allowed hosts usando horizon + IP firewall."""
    allowed_hosts = _get_allowed_hosts()

    with _mikrotik_connection(network_device) as api:
        _remove_rules_by_comment(api, COMMENT_GLOBAL_BLOCK)

        # Aplicar horizon global en todos los puertos del bridge
        _set_all_ports_horizon(api, HORIZON_GLOBAL_BLOCK)
        _ensure_bridge_use_ip_firewall(api)

        # IP firewall – bloqueo global en cadena forward
        ip_filt = _get_ip_filter(api)
        ip_rules = []

        for allowed_ip in allowed_hosts:
            cidr = _to_cidr(allowed_ip)
            ip_rules.append({
                "chain": "forward", "action": "accept",
                "dst-address": cidr, "comment": COMMENT_GLOBAL_BLOCK,
            })
            ip_rules.append({
                "chain": "forward", "action": "accept",
                "src-address": cidr, "comment": COMMENT_GLOBAL_BLOCK,
            })

        ip_rules.append({
            "chain": "forward", "action": "drop",
            "comment": COMMENT_GLOBAL_BLOCK,
        })

        _add_rules_with_placement(ip_filt, ip_rules, "forward")

    logger.info("Bloqueo global (L2+L3) activado en router=%s", network_device.ip_address)


def global_unblock_internet(network_device):
    """Elimina bloqueo global (IP firewall) y restaura horizon."""
    with _mikrotik_connection(network_device) as api:
        _remove_rules_by_comment(api, COMMENT_GLOBAL_BLOCK)
        _set_all_ports_horizon(api, None)
        _disable_bridge_use_ip_firewall_if_clean(api)
    logger.info("Bloqueo global desactivado en router=%s", network_device.ip_address)


def is_global_block_active(network_device):
    try:
        with _mikrotik_connection(network_device) as api:
            filt = _get_bridge_filter(api)
            if any(rule.get("comment", "") == COMMENT_GLOBAL_BLOCK for rule in filt):
                return True
            ip_filt = _get_ip_filter(api)
            return any(rule.get("comment", "") == COMMENT_GLOBAL_BLOCK for rule in ip_filt)
    except MikrotikError:
        return False


# ---------------------------------------------------------------------------
#  Bloqueo / desbloqueo por aula
# ---------------------------------------------------------------------------

def _build_classroom_comment(classroom_id: int) -> str:
    return f"{COMMENT_CLASSROOM_BLOCK}_{classroom_id}"


def classroom_block_internet(classroom_id):
    """Bloquea internet a todos los dispositivos de un aula (horizon por puerto + L3 por IP)."""
    from .models import Device
    comment = _build_classroom_comment(classroom_id)
    allowed_hosts = _get_allowed_hosts()

    devices = (
        Device.objects
        .filter(classroom_id=classroom_id, connected_device__isnull=False)
        .exclude(switch_port__in=["", " "])
        .select_related("connected_device")
    )

    # Agrupar dispositivos por equipo de red para minimizar conexiones
    devices_by_nd = {}
    for device in devices:
        nd = device.connected_device
        if nd.id not in devices_by_nd:
            devices_by_nd[nd.id] = {"network_device": nd, "devices": []}
        devices_by_nd[nd.id]["devices"].append(device)

    for nd_info in devices_by_nd.values():
        nd = nd_info["network_device"]
        dev_list = nd_info["devices"]

        with _mikrotik_connection(nd) as api:
            _remove_rules_by_comment(api, comment)

            # Aplicar horizon del aula en puertos de los dispositivos del aula
            classroom_h = _classroom_horizon(classroom_id)
            for device in dev_list:
                _set_port_horizon(api, device.switch_port, classroom_h)
            _ensure_bridge_use_ip_firewall(api)

            # IP Firewall filter (L3 por IP)
            ip_filt = _get_ip_filter(api)
            ip_rules = []

            for device in dev_list:
                dev_cidr = _to_cidr(str(device.ip))

                for allowed_ip in allowed_hosts:
                    ah_cidr = _to_cidr(allowed_ip)
                    ip_rules.append({
                        "chain": "forward", "action": "accept",
                        "src-address": dev_cidr, "dst-address": ah_cidr,
                        "comment": comment,
                    })
                    ip_rules.append({
                        "chain": "forward", "action": "accept",
                        "src-address": ah_cidr, "dst-address": dev_cidr,
                        "comment": comment,
                    })

                ip_rules.append({
                    "chain": "forward", "action": "drop",
                    "src-address": dev_cidr, "comment": comment,
                })
                ip_rules.append({
                    "chain": "forward", "action": "drop",
                    "dst-address": dev_cidr, "comment": comment,
                })

            _add_rules_with_placement(ip_filt, ip_rules, "forward")

    logger.info("Bloqueo por aula (horizon+L3) activado classroom_id=%s", classroom_id)


def classroom_unblock_internet(classroom_id):
    """Elimina reglas de bloqueo de aula (IP) y restaura horizon de puertos del aula."""
    from .models import Device

    comment = _build_classroom_comment(classroom_id)

    devices = (
        Device.objects
        .filter(classroom_id=classroom_id, connected_device__isnull=False)
        .exclude(switch_port__in=["", " "])
        .select_related("connected_device")
    )
    ports_by_nd = {}
    for d in devices:
        nd = d.connected_device
        ports_by_nd.setdefault(nd.id, {"network_device": nd, "ports": set()})
        ports_by_nd[nd.id]["ports"].add(d.switch_port)

    for nd in NetworkDevice.objects.all():
        try:
            with _mikrotik_connection(nd) as api:
                _remove_rules_by_comment(api, comment)
                nd_info = ports_by_nd.get(nd.id)
                if nd_info:
                    for port in nd_info["ports"]:
                        _set_port_horizon(api, port, None)
                _disable_bridge_use_ip_firewall_if_clean(api)
        except MikrotikError as e:
            logger.warning("Fallo en router %s desbloqueando aula %s: %s", nd.ip_address, classroom_id, e)
    logger.info("Bloqueo por aula desactivado classroom_id=%s", classroom_id)


def is_classroom_block_active(classroom_id):
    comment = _build_classroom_comment(classroom_id)
    for nd in NetworkDevice.objects.all():
        try:
            with _mikrotik_connection(nd) as api:
                filt = _get_bridge_filter(api)
                if any(rule.get("comment", "") == comment for rule in filt):
                    return True
                ip_filt = _get_ip_filter(api)
                if any(rule.get("comment", "") == comment for rule in ip_filt):
                    return True
        except MikrotikError:
            pass
    return False


def find_device_network_info(mac):
    mac_upper = mac.strip().upper()
    found_device_arp = None

    for network_device in NetworkDevice.objects.all():
        try:
            with _mikrotik_connection(network_device) as api:
                # Mirar en la tabla L2 del Switch con una expresion generadora rapida
                try:
                    bridge_hosts = api.path("/interface/bridge/host")
                    host_entry = next((h for h in bridge_hosts if h.get("mac-address", "").upper() == mac_upper), None)
                    
                    if host_entry:
                        switch_port = host_entry.get("on-interface", "")
                        logger.info("Mac=%s en L2 router=%s puerto=%s", mac, network_device.ip_address, switch_port)
                        return network_device, switch_port
                except Exception as e:
                    logger.debug("Error consultando bridge hosts en %s: %s", network_device.ip_address, e)

                # Buscar en ARP  si no se encontro el puerto fisico en ningun switch previo
                if not found_device_arp:
                    try:
                        arp_path = api.path("/ip/arp")
                        arp_entry = next((a for a in arp_path if a.get("mac-address", "").upper() == mac_upper), None)
                        if arp_entry:
                            found_device_arp = network_device
                    except Exception:
                        pass

        except MikrotikError as e:
            logger.warning("Fallo en router %s buscando mac %s: %s", network_device.ip_address, mac, e)

    # Si terminamos todos los equipos y solo encontramos registro ARP
    if found_device_arp:
        logger.info("Mac=%s SOLO en ARP en router=%s", mac, found_device_arp.ip_address)
        return found_device_arp, ""

    return None, ""