# Servicio de comunicacion con la API de RouterOS de MikroTik
# Gestiona reglas de bridge filter (Capa 2) para bloquear y desbloquear
# el acceso a internet y el trafico entre dispositivos de la misma subred
# El bloqueo se realiza por PUERTO FISICO del bridge (in-interface / out-interface)
# usando /interface/bridge/filter en lugar de /ip/firewall/filter
# Esto garantiza aislamiento total: ni internet, ni otras subredes, ni trafico local
# Las reglas se identifican mediante comentarios con el prefijo MONITOR
# para poder localizarlas y eliminarlas de forma segura
import logging
from contextlib import contextmanager

from librouteros import connect

from .models import NetworkDevice, AllowedHost

logger = logging.getLogger("devices.mikrotik")

# Prefijos de comentario para identificar las reglas creadas por el sistema
COMMENT_PREFIX = "MONITOR"
COMMENT_DEVICE_BLOCK = f"{COMMENT_PREFIX}_BLOCK"
COMMENT_GLOBAL_BLOCK = f"{COMMENT_PREFIX}_GLOBAL_BLOCK"
COMMENT_CLASSROOM_BLOCK = f"{COMMENT_PREFIX}_CLASS_BLOCK"


# Excepcion personalizada para errores de comunicacion con el router
class MikrotikError(Exception):
    pass


# Obtiene la lista de IPs de los hosts permitidos desde la base de datos
def _get_allowed_hosts():
    return list(AllowedHost.objects.values_list("ip_address", flat=True))


# Formatea una IP como direccion CIDR con /32
# El bridge filter de RouterOS exige notacion CIDR para src-address y dst-address
# a diferencia del firewall filter que acepta IPs planas
def _to_cidr(ip: str) -> str:
    ip_str = str(ip)
    if "/" not in ip_str:
        return f"{ip_str}/32"
    return ip_str


# Abre y cierra la conexion con el router MikroTik de forma segura
@contextmanager
def _mikrotik_connection(network_device: NetworkDevice):
    try:
        api = connect(
            host=str(network_device.ip_address),
            username=network_device.username,
            password=network_device.password,
            port=network_device.api_port,
        )
    except Exception as exc:
        raise MikrotikError(
            f"No se pudo conectar al router {network_device.ip_address}: {exc}"
        ) from exc
    try:
        yield api
    finally:
        api.close()


# Devuelve el recurso de reglas de filtrado del bridge (Capa 2)
def _get_bridge_filter(api):
    return api.path("/interface/bridge/filter")


# Genera el comentario identificador para reglas de bloqueo individual
def _build_device_comment(device_id: int) -> str:
    return f"{COMMENT_DEVICE_BLOCK}_{device_id}"


# Elimina todas las reglas del bridge filter que coincidan con el comentario dado
# Recorre la lista completa de reglas y borra las coincidentes en orden inverso
# para no alterar los indices internos durante el borrado
def _remove_rules_by_comment(api, comment: str):
    filt = _get_bridge_filter(api)

    # Recoge los IDs de las reglas que coinciden con el comentario
    rules_to_remove = [
        rule[".id"] for rule in filt
        if rule.get("comment", "") == comment
    ]

    # Elimina en orden inverso para no desplazar indices
    for rule_id in reversed(rules_to_remove):
        filt.remove(rule_id)
        logger.info("Regla eliminada: id=%s comment=%s", rule_id, comment)


# Obtiene el ID interno de la primera regla del chain forward
# Se utiliza para insertar nuevas reglas antes de las existentes
def _get_first_forward_rule_id(api):
    filt = _get_bridge_filter(api)
    for rule in filt:
        if rule.get("chain") == "forward":
            return rule[".id"]
    return None


# Bloquea completamente un dispositivo a nivel de Capa 2 por su PUERTO del bridge
# Crea reglas en /interface/bridge/filter que aseguran aislamiento total:
# ni acceso a internet, ni a otras subredes, ni trafico dentro de la subred local
# Solo se permite la comunicacion con los hosts explicitamente autorizados
def block_device_internet(network_device, switch_port, device_id):
    comment = _build_device_comment(device_id)
    allowed_hosts = _get_allowed_hosts()

    with _mikrotik_connection(network_device) as api:
        # Elimina reglas previas del mismo dispositivo para evitar duplicados
        _remove_rules_by_comment(api, comment)

        filt = _get_bridge_filter(api)
        first_rule_id = _get_first_forward_rule_id(api)

        rules = []

        # Permite trafico ARP en ambas direcciones para el puerto
        # Sin ARP el dispositivo no podria resolver las IPs de los hosts
        # permitidos y la comunicacion IP seria imposible
        rules.append({
            "chain": "forward", "action": "accept",
            "in-interface": switch_port,
            "mac-protocol": "arp",
            "comment": comment,
        })
        rules.append({
            "chain": "forward", "action": "accept",
            "out-interface": switch_port,
            "mac-protocol": "arp",
            "comment": comment,
        })

        # Para cada host permitido crea reglas accept en ambas direcciones
        # mac-protocol=ip es obligatorio en bridge filter para que RouterOS
        # evalue los campos src-address y dst-address a nivel de Capa 3
        for allowed_ip in allowed_hosts:
            # Trafico IP que sale del puerto hacia el host permitido
            rules.append({
                "chain": "forward", "action": "accept",
                "in-interface": switch_port,
                "mac-protocol": "ip",
                "dst-address": _to_cidr(allowed_ip),
                "comment": comment,
            })
            # Trafico IP del host permitido que entra al puerto
            rules.append({
                "chain": "forward", "action": "accept",
                "out-interface": switch_port,
                "mac-protocol": "ip",
                "src-address": _to_cidr(allowed_ip),
                "comment": comment,
            })

        # Bloquea TODO el trafico restante que sale del puerto (Capa 2 completa)
        rules.append({
            "chain": "forward", "action": "drop",
            "in-interface": switch_port,
            "comment": comment,
        })
        # Bloquea TODO el trafico restante que entra al puerto (Capa 2 completa)
        rules.append({
            "chain": "forward", "action": "drop",
            "out-interface": switch_port,
            "comment": comment,
        })

        # Inserta cada regla antes de la primera regla forward existente
        # para garantizar que se evaluen con prioridad sobre las demas
        for rule_params in rules:
            if first_rule_id:
                rule_params["place-before"] = first_rule_id
            filt.add(**rule_params)

    logger.info(
        "Internet bloqueado (L2) para device_id=%s puerto=%s (hosts permitidos: %s)",
        device_id, switch_port, allowed_hosts,
    )


# Elimina todas las reglas de bloqueo individual de un dispositivo
def unblock_device_internet(network_device, device_id):
    comment = _build_device_comment(device_id)

    with _mikrotik_connection(network_device) as api:
        _remove_rules_by_comment(api, comment)

    logger.info("Internet desbloqueado para device_id=%s", device_id)


# Activa el bloqueo global a nivel de Capa 2 en el router
# Crea reglas en /interface/bridge/filter que aislan todos los puertos
# Solo se permite trafico hacia y desde los hosts autorizados
def global_block_internet(network_device):
    allowed_hosts = _get_allowed_hosts()

    with _mikrotik_connection(network_device) as api:
        # Elimina reglas globales previas para evitar duplicados
        _remove_rules_by_comment(api, COMMENT_GLOBAL_BLOCK)

        filt = _get_bridge_filter(api)
        first_rule_id = _get_first_forward_rule_id(api)

        rules = []

        # Permite trafico ARP globalmente para que la resolucion de
        # direcciones funcione y los hosts permitidos sean alcanzables
        rules.append({
            "chain": "forward", "action": "accept",
            "mac-protocol": "arp",
            "comment": COMMENT_GLOBAL_BLOCK,
        })

        # Permite trafico IP hacia y desde cada host autorizado
        # mac-protocol=ip es obligatorio para evaluar direcciones IP en bridge filter
        for allowed_ip in allowed_hosts:
            rules.append({
                "chain": "forward", "action": "accept",
                "mac-protocol": "ip",
                "dst-address": _to_cidr(allowed_ip),
                "comment": COMMENT_GLOBAL_BLOCK,
            })
            rules.append({
                "chain": "forward", "action": "accept",
                "mac-protocol": "ip",
                "src-address": _to_cidr(allowed_ip),
                "comment": COMMENT_GLOBAL_BLOCK,
            })

        # Bloquea todo el trafico forward restante a nivel de Capa 2
        rules.append({
            "chain": "forward", "action": "drop",
            "comment": COMMENT_GLOBAL_BLOCK,
        })

        # Inserta todas las reglas al inicio del chain forward
        # para que prevalezcan sobre cualquier regla existente
        for rule_params in rules:
            if first_rule_id:
                rule_params["place-before"] = first_rule_id
            filt.add(**rule_params)

    logger.info(
        "Bloqueo global (L2) activado en router=%s (hosts permitidos: %s)",
        network_device.ip_address, allowed_hosts,
    )


# Elimina todas las reglas de bloqueo global del router
def global_unblock_internet(network_device):
    with _mikrotik_connection(network_device) as api:
        _remove_rules_by_comment(api, COMMENT_GLOBAL_BLOCK)

    logger.info(
        "Bloqueo global desactivado en router=%s",
        network_device.ip_address,
    )


# Comprueba si existe algun bloqueo global activo en el router
# Busca reglas con el comentario MONITOR_GLOBAL_BLOCK en el bridge filter
def is_global_block_active(network_device):
    with _mikrotik_connection(network_device) as api:
        filt = _get_bridge_filter(api)
        for rule in filt:
            if rule.get("comment", "") == COMMENT_GLOBAL_BLOCK:
                return True
    return False


# Genera el comentario identificador para reglas de bloqueo por aula
def _build_classroom_comment(classroom_id: int) -> str:
    return f"{COMMENT_CLASSROOM_BLOCK}_{classroom_id}"


# Bloquea el internet de todos los dispositivos de un aula a nivel de Capa 2
# Agrupa los dispositivos por equipo de red y crea reglas de bridge filter
# por cada puerto fisico asociado a los dispositivos del aula
def classroom_block_internet(classroom_id):
    from .models import Device

    comment = _build_classroom_comment(classroom_id)
    allowed_hosts = _get_allowed_hosts()

    # Obtiene los dispositivos del aula con equipo de red y puerto asignados
    devices = (
        Device.objects.filter(
            classroom_id=classroom_id,
            connected_device__isnull=False,
        )
        .exclude(switch_port__in=["", " "])
        .select_related("connected_device")
    )

    # Agrupa los dispositivos por equipo de red
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
            # Elimina reglas previas de esta aula en este equipo de red
            _remove_rules_by_comment(api, comment)

            filt = _get_bridge_filter(api)
            first_rule_id = _get_first_forward_rule_id(api)

            rules = []

            for port in ports:
                # Permite trafico ARP en ambas direcciones para el puerto
                rules.append({
                    "chain": "forward", "action": "accept",
                    "in-interface": port,
                    "mac-protocol": "arp",
                    "comment": comment,
                })
                rules.append({
                    "chain": "forward", "action": "accept",
                    "out-interface": port,
                    "mac-protocol": "arp",
                    "comment": comment,
                })

                # Permite trafico IP hacia y desde cada host autorizado
                for allowed_ip in allowed_hosts:
                    rules.append({
                        "chain": "forward", "action": "accept",
                        "in-interface": port,
                        "mac-protocol": "ip",
                        "dst-address": _to_cidr(allowed_ip),
                        "comment": comment,
                    })
                    rules.append({
                        "chain": "forward", "action": "accept",
                        "out-interface": port,
                        "mac-protocol": "ip",
                        "src-address": _to_cidr(allowed_ip),
                        "comment": comment,
                    })

                # Bloquea todo el trafico restante en el puerto
                rules.append({
                    "chain": "forward", "action": "drop",
                    "in-interface": port,
                    "comment": comment,
                })
                rules.append({
                    "chain": "forward", "action": "drop",
                    "out-interface": port,
                    "comment": comment,
                })

            # Inserta las reglas al inicio del chain forward
            for rule_params in rules:
                if first_rule_id:
                    rule_params["place-before"] = first_rule_id
                filt.add(**rule_params)

    logger.info(
        "Bloqueo por aula (L2) activado classroom_id=%s (hosts permitidos: %s)",
        classroom_id, allowed_hosts,
    )


# Elimina todas las reglas de bloqueo por aula de todos los equipos de red
def classroom_unblock_internet(classroom_id):
    comment = _build_classroom_comment(classroom_id)

    for nd in NetworkDevice.objects.all():
        try:
            with _mikrotik_connection(nd) as api:
                _remove_rules_by_comment(api, comment)
        except MikrotikError:
            logger.warning(
                "No se pudo conectar a %s para desbloquear aula %s",
                nd.ip_address, classroom_id,
            )

    logger.info(
        "Bloqueo por aula desactivado classroom_id=%s", classroom_id,
    )


# Comprueba si existe bloqueo activo para un aula en algun equipo de red
def is_classroom_block_active(classroom_id):
    comment = _build_classroom_comment(classroom_id)

    for nd in NetworkDevice.objects.all():
        try:
            with _mikrotik_connection(nd) as api:
                filt = _get_bridge_filter(api)
                for rule in filt:
                    if rule.get("comment", "") == comment:
                        return True
        except MikrotikError:
            continue
    return False


# Busca en que equipo de red esta conectado un dispositivo por su MAC
# Consulta la tabla ARP de cada NetworkDevice registrado en la base de datos
# Si encuentra la MAC devuelve el NetworkDevice y el puerto del bridge
def find_device_network_info(mac):
    # Normaliza la MAC a mayusculas con dos puntos para comparar con RouterOS
    mac_upper = mac.upper()

    for network_device in NetworkDevice.objects.all():
        try:
            with _mikrotik_connection(network_device) as api:
                # Busca la MAC en la tabla ARP del router
                arp_path = api.path("/ip/arp")
                found_in_arp = False

                for entry in arp_path:
                    entry_mac = entry.get("mac-address", "").upper()
                    if entry_mac == mac_upper:
                        found_in_arp = True
                        break

                if not found_in_arp:
                    continue

                # Si la MAC esta en el ARP busca el puerto fisico en la tabla del bridge
                switch_port = ""
                try:
                    bridge_hosts = api.path("/interface/bridge/host")
                    for host in bridge_hosts:
                        host_mac = host.get("mac-address", "").upper()
                        if host_mac == mac_upper:
                            switch_port = host.get("on-interface", "")
                            break
                except Exception:
                    # Si el router no tiene bridge configurado se ignora
                    logger.debug(
                        "No se pudo consultar bridge hosts en %s",
                        network_device.ip_address,
                    )

                logger.info(
                    "Dispositivo mac=%s encontrado en router=%s puerto=%s",
                    mac, network_device.ip_address, switch_port or "desconocido",
                )
                return network_device, switch_port

        except MikrotikError:
            logger.warning(
                "No se pudo conectar a %s para buscar mac=%s",
                network_device.ip_address, mac,
            )
            continue

    return None, ""
