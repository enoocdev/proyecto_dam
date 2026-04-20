import logging
import ssl
from contextlib import contextmanager

from librouteros import connect

from .models import NetworkDevice, AllowedHost

logger = logging.getLogger("devices.mikrotik")

COMMENT_PREFIX = "MONITOR"
COMMENT_DEVICE_BLOCK = f"{COMMENT_PREFIX}_BLOCK"
COMMENT_GLOBAL_BLOCK = f"{COMMENT_PREFIX}_GLOBAL_BLOCK"


class MikrotikError(Exception):
    pass


def _get_allowed_hosts(classroom_id=None):
    """Devuelve IPs de hosts permitidos: los globales (sin aula) mas los del aula indicada."""
    from django.db.models import Q
    qs = AllowedHost.objects.filter(
        Q(classroom__isnull=True) | Q(classroom_id=classroom_id)
    ) if classroom_id else AllowedHost.objects.filter(classroom__isnull=True)
    return list(qs.values_list("ip_address", flat=True))


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


def _get_ip_filter(api):
    """Accede a la tabla de reglas del firewall IP (/ip/firewall/filter)."""
    return api.path("/ip/firewall/filter")


def _get_bridge_filter(api):
    """Accede a la tabla de reglas del bridge filter (/interface/bridge/filter)."""
    return api.path("/interface/bridge/filter")


def _set_hw_offload(api, port_name: str, enabled: bool):
    """Activa o desactiva hw-offload en un puerto del bridge.
    Con hw-offload=yes el trafico lo gestiona el chip del switch y las reglas
    de bridge filter NO se aplican. Hay que desactivarlo para filtrar L2."""
    bridge_ports = api.path("/interface/bridge/port")
    value = "yes" if enabled else "no"
    for port in bridge_ports:
        if port.get("interface") == port_name:
            try:
                bridge_ports.update(**{".id": port[".id"], "hw": value})
                logger.info("hw-offload=%s en puerto %s", value, port_name)
            except Exception as e:
                logger.warning("No se pudo cambiar hw-offload en %s: %s", port_name, e)
            return
    logger.debug("Puerto %s no encontrado en bridge ports (hw-offload)", port_name)


def _set_all_hw_offload(api, enabled: bool):
    """Activa o desactiva hw-offload en todos los puertos del bridge."""
    bridge_ports = api.path("/interface/bridge/port")
    value = "yes" if enabled else "no"
    entries = [(p[".id"], p.get("interface", "?")) for p in bridge_ports]
    for pid, iface in entries:
        try:
            bridge_ports.update(**{".id": pid, "hw": value})
        except Exception as e:
            logger.warning("No se pudo cambiar hw-offload en %s: %s", iface, e)
    if entries:
        logger.info("hw-offload=%s en %d puertos del bridge", value, len(entries))


def _build_device_comment(device_id: int) -> str:
    return f"{COMMENT_DEVICE_BLOCK}_{device_id}"


def _remove_rules_by_comment(api, comment: str):
    """Elimina reglas con el comentario dado de IP firewall filter y bridge filter."""
    # Limpiar IP firewall filter
    ip_filt = _get_ip_filter(api)
    ip_rules_to_remove = [rule[".id"] for rule in ip_filt if rule.get("comment", "") == comment]
    for rule_id in reversed(ip_rules_to_remove):
        ip_filt.remove(rule_id)
        logger.info("Regla IP firewall eliminada: id=%s comment=%s", rule_id, comment)

    # Limpiar bridge filter
    br_filt = _get_bridge_filter(api)
    br_rules_to_remove = [rule[".id"] for rule in br_filt if rule.get("comment", "") == comment]
    for rule_id in reversed(br_rules_to_remove):
        br_filt.remove(rule_id)
        logger.info("Regla bridge eliminada: id=%s comment=%s", rule_id, comment)


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


#  Bloqueo / desbloqueo de un dispositivo individual

def block_device_internet(network_device, switch_port, device_id, device_ip, classroom_id=None):
    """Bloquea internet a un dispositivo usando reglas de IP firewall (por IP)
    y bridge filter (por puerto fisico del switch) para evitar que VMs en
    adaptador puente puedan saltarse el bloqueo."""

    comment = _build_device_comment(device_id)
    allowed_hosts = _get_allowed_hosts(classroom_id=classroom_id)

    with _mikrotik_connection(network_device) as api:
        _remove_rules_by_comment(api, comment)

        # --- L3: IP Firewall Filter (bloqueo por IP) ---
        ip_filt = _get_ip_filter(api)
        ip_rules = []
        dev_cidr = _to_cidr(device_ip)

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

        # --- L2: Bridge Filter (bloqueo por puerto fisico) ---
        _set_hw_offload(api, switch_port, False)

        br_filt = _get_bridge_filter(api)
        br_rules = []

        for allowed_ip in allowed_hosts:
            ah_cidr = _to_cidr(allowed_ip)
            br_rules.append({
                "chain": "forward", "action": "accept",
                "in-interface": switch_port, "mac-protocol": "ip",
                "dst-address": ah_cidr,
                "comment": comment,
            })

        br_rules.append({
            "chain": "forward", "action": "drop",
            "in-interface": switch_port,
            "comment": comment,
        })

        _add_rules_with_placement(br_filt, br_rules, "forward")

    logger.info(
        "Internet bloqueado (IP+puerto) para device_id=%s ip=%s puerto=%s",
        device_id, device_ip, switch_port,
    )


def unblock_device_internet(network_device, device_id):
    """Desbloquea internet eliminando reglas de IP firewall y bridge filter
    del dispositivo (MONITOR_BLOCK_X)."""
    from .models import Device
    comment = _build_device_comment(device_id)

    try:
        device = Device.objects.get(id=device_id)
        switch_port = device.switch_port.strip() if device.switch_port else ""
    except Device.DoesNotExist:
        switch_port = ""

    with _mikrotik_connection(network_device) as api:
        _remove_rules_by_comment(api, comment)

        if switch_port:
            _set_hw_offload(api, switch_port, True)

    logger.info("Internet desbloqueado para device_id=%s", device_id)


#  Bloqueo / desbloqueo global por equipo de red

def global_block_internet(network_device):
    """Bloquea todo el trafico (IP firewall + bridge filter) excepto allowed hosts."""
    allowed_hosts = _get_allowed_hosts()

    with _mikrotik_connection(network_device) as api:
        _remove_rules_by_comment(api, COMMENT_GLOBAL_BLOCK)

        # --- L3: IP Firewall Filter ---
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

        # --- L2: Bridge Filter (bloqueo global por bridge) ---
        _set_all_hw_offload(api, False)

        br_filt = _get_bridge_filter(api)
        br_rules = []

        for allowed_ip in allowed_hosts:
            cidr = _to_cidr(allowed_ip)
            br_rules.append({
                "chain": "forward", "action": "accept",
                "mac-protocol": "ip", "dst-address": cidr,
                "comment": COMMENT_GLOBAL_BLOCK,
            })

        br_rules.append({
            "chain": "forward", "action": "drop",
            "comment": COMMENT_GLOBAL_BLOCK,
        })

        _add_rules_with_placement(br_filt, br_rules, "forward")

    logger.info("Bloqueo global (IP+bridge) activado en router=%s", network_device.ip_address)


def global_unblock_internet(network_device):
    """Elimina bloqueo global y restaura hw-offload."""
    with _mikrotik_connection(network_device) as api:
        _remove_rules_by_comment(api, COMMENT_GLOBAL_BLOCK)
        _set_all_hw_offload(api, True)
    logger.info("Bloqueo global desactivado en router=%s", network_device.ip_address)


def is_global_block_active(network_device):
    try:
        with _mikrotik_connection(network_device) as api:
            ip_filt = _get_ip_filter(api)
            if any(rule.get("comment", "") == COMMENT_GLOBAL_BLOCK for rule in ip_filt):
                return True
            br_filt = _get_bridge_filter(api)
            return any(rule.get("comment", "") == COMMENT_GLOBAL_BLOCK for rule in br_filt)
    except MikrotikError:
        return False


#  Bloqueo / desbloqueo por aula
#  Reutiliza block_device_internet / unblock_device_internet por cada equipo
#  para que las reglas sean identicas a las individuales (MONITOR_BLOCK_X)
#  y desbloquear un equipo suelto funcione sin logica extra.


def classroom_block_internet(classroom_id):
    """Bloquea internet a cada dispositivo del aula llamando al bloqueo individual."""
    from .models import Device

    devices = (
        Device.objects
        .filter(classroom_id=classroom_id, connected_device__isnull=False)
        .exclude(switch_port__in=["", " "])
        .select_related("connected_device")
    )

    for device in devices:
        try:
            block_device_internet(
                network_device=device.connected_device,
                switch_port=device.switch_port,
                device_id=device.id,
                device_ip=str(device.ip),
                classroom_id=classroom_id,
            )
        except MikrotikError as e:
            logger.warning(
                "Fallo al bloquear device_id=%s en aula %s: %s",
                device.id, classroom_id, e,
            )

    logger.info("Bloqueo por aula activado classroom_id=%s", classroom_id)


def classroom_unblock_internet(classroom_id):
    """Desbloquea internet de cada dispositivo del aula llamando al desbloqueo individual."""
    from .models import Device

    devices = (
        Device.objects
        .filter(classroom_id=classroom_id, connected_device__isnull=False)
        .exclude(switch_port__in=["", " "])
        .select_related("connected_device")
    )

    for device in devices:
        try:
            unblock_device_internet(
                network_device=device.connected_device,
                device_id=device.id,
            )
        except MikrotikError as e:
            logger.warning(
                "Fallo al desbloquear device_id=%s en aula %s: %s",
                device.id, classroom_id, e,
            )

    logger.info("Bloqueo por aula desactivado classroom_id=%s", classroom_id)


# ======================================================================
#  Busqueda de dispositivo en la red
# ======================================================================

def find_device_network_info(mac):
    mac_upper = mac.strip().upper()
    found_device_arp = None

    for network_device in NetworkDevice.objects.all():
        try:
            with _mikrotik_connection(network_device) as api:
                try:
                    bridge_hosts = api.path("/interface/bridge/host")
                    host_entry = next((h for h in bridge_hosts if h.get("mac-address", "").upper() == mac_upper), None)

                    if host_entry:
                        switch_port = host_entry.get("on-interface", "")
                        logger.info("Mac=%s en L2 router=%s puerto=%s", mac, network_device.ip_address, switch_port)
                        return network_device, switch_port
                except Exception as e:
                    logger.debug("Error consultando bridge hosts en %s: %s", network_device.ip_address, e)

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

    if found_device_arp:
        logger.info("Mac=%s SOLO en ARP en router=%s", mac, found_device_arp.ip_address)
        return found_device_arp, ""

    return None, ""
