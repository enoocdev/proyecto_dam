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


def _build_device_comment(device_id: int) -> str:
    return f"{COMMENT_DEVICE_BLOCK}_{device_id}"


def _remove_rules_by_comment(api, comment: str):
    filt = _get_bridge_filter(api)
    rules_to_remove = [rule[".id"] for rule in filt if rule.get("comment", "") == comment]
    
    for rule_id in reversed(rules_to_remove):
        filt.remove(rule_id)
        logger.info("Regla eliminada: id=%s comment=%s", rule_id, comment)


def _get_first_forward_rule_id(api):
    filt = _get_bridge_filter(api)
    # Busca la primera regla forward eficientemente sin bucles for tradicionales
    rule = next((r for r in filt if r.get("chain") == "forward"), None)
    return rule[".id"] if rule else None


def block_device_internet(network_device, switch_port, device_id):
    comment = _build_device_comment(device_id)
    allowed_hosts = _get_allowed_hosts()

    with _mikrotik_connection(network_device) as api:
        _remove_rules_by_comment(api, comment)
        filt = _get_bridge_filter(api)
        first_rule_id = _get_first_forward_rule_id(api)
        rules = []

        rules.append({"chain": "prerouting", "action": "accept", "in-interface": switch_port, "mac-protocol": "arp", "comment": comment})
        rules.append({"chain": "forward", "action": "accept", "out-interface": switch_port, "mac-protocol": "arp", "comment": comment})

        for allowed_ip in allowed_hosts:
            rules.append({"chain": "prerouting", "action": "accept", "in-interface": switch_port, "mac-protocol": "ip", "dst-address": _to_cidr(allowed_ip), "comment": comment})
            rules.append({"chain": "forward", "action": "accept", "out-interface": switch_port, "mac-protocol": "ip", "src-address": _to_cidr(allowed_ip), "comment": comment})

        rules.append({"chain": "prerouting", "action": "drop", "in-interface": switch_port, "comment": comment})
        rules.append({"chain": "forward", "action": "drop", "out-interface": switch_port, "comment": comment})

        for rule_params in rules:
            if first_rule_id:
                rule_params["place-before"] = first_rule_id
            filt.add(**rule_params)

    logger.info("Internet bloqueado (L2) para device_id=%s puerto=%s", device_id, switch_port)


def unblock_device_internet(network_device, device_id):
    comment = _build_device_comment(device_id)
    with _mikrotik_connection(network_device) as api:
        _remove_rules_by_comment(api, comment)
    logger.info("Internet desbloqueado para device_id=%s", device_id)


def global_block_internet(network_device):
    allowed_hosts = _get_allowed_hosts()

    with _mikrotik_connection(network_device) as api:
        _remove_rules_by_comment(api, COMMENT_GLOBAL_BLOCK)
        filt = _get_bridge_filter(api)
        first_rule_id = _get_first_forward_rule_id(api)
        rules = []

        rules.append({"chain": "prerouting", "action": "accept", "mac-protocol": "arp", "comment": COMMENT_GLOBAL_BLOCK})
        
        for allowed_ip in allowed_hosts:
            rules.append({"chain": "prerouting", "action": "accept", "mac-protocol": "ip", "dst-address": _to_cidr(allowed_ip), "comment": COMMENT_GLOBAL_BLOCK})
            rules.append({"chain": "prerouting", "action": "accept", "mac-protocol": "ip", "src-address": _to_cidr(allowed_ip), "comment": COMMENT_GLOBAL_BLOCK})
        
        rules.append({"chain": "prerouting", "action": "drop", "comment": COMMENT_GLOBAL_BLOCK})

        for rule_params in rules:
            if first_rule_id:
                rule_params["place-before"] = first_rule_id
            filt.add(**rule_params)

    logger.info("Bloqueo global (L2) activado en router=%s", network_device.ip_address)


def global_unblock_internet(network_device):
    with _mikrotik_connection(network_device) as api:
        _remove_rules_by_comment(api, COMMENT_GLOBAL_BLOCK)
    logger.info("Bloqueo global desactivado en router=%s", network_device.ip_address)


def is_global_block_active(network_device):
    try:
        with _mikrotik_connection(network_device) as api:
            filt = _get_bridge_filter(api)
            # Retorna True al instante si encuentra alguna regla con ese comentario
            return any(rule.get("comment", "") == COMMENT_GLOBAL_BLOCK for rule in filt)
    except MikrotikError:
        return False


def _build_classroom_comment(classroom_id: int) -> str:
    return f"{COMMENT_CLASSROOM_BLOCK}_{classroom_id}"


def classroom_block_internet(classroom_id):
    from .models import Device
    comment = _build_classroom_comment(classroom_id)
    allowed_hosts = _get_allowed_hosts()

    devices = (Device.objects.filter(classroom_id=classroom_id, connected_device__isnull=False)
               .exclude(switch_port__in=["", " "]).select_related("connected_device"))

    devices_by_nd = {}
    for device in devices:
        nd = device.connected_device
        if nd.id not in devices_by_nd:
            devices_by_nd[nd.id] = {"network_device": nd, "ports": set()}
        devices_by_nd[nd.id]["ports"].add(device.switch_port)

    for nd_info in devices_by_nd.values():
        nd = nd_info["network_device"]
        ports = nd_info["ports"]

        with _mikrotik_connection(nd) as api:
            _remove_rules_by_comment(api, comment)
            filt = _get_bridge_filter(api)
            first_rule_id = _get_first_forward_rule_id(api)
            rules = []

            for port in ports:
                rules.append({"chain": "prerouting", "action": "accept", "in-interface": port, "mac-protocol": "arp", "comment": comment})
                rules.append({"chain": "forward", "action": "accept", "out-interface": port, "mac-protocol": "arp", "comment": comment})

                for allowed_ip in allowed_hosts:
                    rules.append({"chain": "prerouting", "action": "accept", "in-interface": port, "mac-protocol": "ip", "dst-address": _to_cidr(allowed_ip), "comment": comment})
                    rules.append({"chain": "forward", "action": "accept", "out-interface": port, "mac-protocol": "ip", "src-address": _to_cidr(allowed_ip), "comment": comment})

                rules.append({"chain": "prerouting", "action": "drop", "in-interface": port, "comment": comment})
                rules.append({"chain": "forward", "action": "drop", "out-interface": port, "comment": comment})

            for rule_params in rules:
                if first_rule_id:
                    rule_params["place-before"] = first_rule_id
                filt.add(**rule_params)

    logger.info("Bloqueo por aula (L2) activado classroom_id=%s", classroom_id)


def classroom_unblock_internet(classroom_id):
    comment = _build_classroom_comment(classroom_id)
    for nd in NetworkDevice.objects.all():
        try:
            with _mikrotik_connection(nd) as api:
                _remove_rules_by_comment(api, comment)
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