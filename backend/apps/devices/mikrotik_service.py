# Servicio de comunicacion con la API de RouterOS de MikroTik
# Gestiona reglas de firewall para bloquear y desbloquear el acceso a internet
# Las reglas se identifican mediante comentarios con el prefijo MONITOR
# para poder localizarlas y eliminarlas de forma segura
import logging
from contextlib import contextmanager

from librouteros import connect
from django.conf import settings

from .models import NetworkDevice

logger = logging.getLogger("devices.mikrotik")

# Prefijos de comentario para identificar las reglas creadas por el sistema
COMMENT_PREFIX = "MONITOR"
COMMENT_DEVICE_BLOCK = f"{COMMENT_PREFIX}_BLOCK"
COMMENT_GLOBAL_BLOCK = f"{COMMENT_PREFIX}_GLOBAL_BLOCK"


# Excepcion personalizada para errores de comunicacion con el router
class MikrotikError(Exception):
    pass


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


# Devuelve el recurso de reglas de filtrado del firewall
def _get_firewall_filter(api):
    return api.path("/ip/firewall/filter")


# Genera el comentario identificador para reglas de bloqueo individual
def _build_device_comment(device_id: int) -> str:
    return f"{COMMENT_DEVICE_BLOCK}_{device_id}"


# Elimina todas las reglas de firewall que coincidan con el comentario dado
# Recorre la lista completa de reglas y borra las coincidentes en orden inverso
# para no alterar los indices internos durante el borrado
def _remove_rules_by_comment(api, comment: str):
    filt = _get_firewall_filter(api)

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
    filt = _get_firewall_filter(api)
    for rule in filt:
        if rule.get("chain") == "forward":
            return rule[".id"]
    return None


# Bloquea el acceso a internet de un dispositivo especifico
# Crea reglas que permiten solo la comunicacion con el host autorizado
# y deniegan todo el trafico restante insertandolas al inicio del chain forward
def block_device_internet(network_device, device_ip, device_id, allowed_host=None):
    comment = _build_device_comment(device_id)
    allowed = allowed_host or settings.MIKROTIK_ALLOWED_HOST

    with _mikrotik_connection(network_device) as api:
        # Elimina reglas previas del mismo dispositivo para evitar duplicados
        _remove_rules_by_comment(api, comment)

        filt = _get_firewall_filter(api)
        first_rule_id = _get_first_forward_rule_id(api)

        # Reglas ordenadas: primero permitir trafico al host autorizado
        # despues denegar todo lo demas del dispositivo
        # Se usan diccionarios porque los parametros de RouterOS llevan guiones
        rules = [
            # Permite trafico del dispositivo al host autorizado
            {
                "chain": "forward", "action": "accept",
                "src-address": device_ip, "dst-address": allowed,
                "comment": comment,
            },
            # Permite trafico del host autorizado al dispositivo
            {
                "chain": "forward", "action": "accept",
                "src-address": allowed, "dst-address": device_ip,
                "comment": comment,
            },
            # Bloquea todo el trafico saliente del dispositivo
            {
                "chain": "forward", "action": "drop",
                "src-address": device_ip,
                "comment": comment,
            },
            # Bloquea todo el trafico entrante al dispositivo
            {
                "chain": "forward", "action": "drop",
                "dst-address": device_ip,
                "comment": comment,
            },
        ]

        # Inserta cada regla antes de la primera regla forward existente
        # para garantizar que se evaluen con prioridad sobre las demas
        for rule_params in rules:
            if first_rule_id:
                rule_params["place-before"] = first_rule_id
            filt.add(**rule_params)

    logger.info(
        "Internet bloqueado para device_id=%s ip=%s (permitido: %s)",
        device_id, device_ip, allowed,
    )


# Elimina todas las reglas de bloqueo individual de un dispositivo
def unblock_device_internet(network_device, device_id):
    comment = _build_device_comment(device_id)

    with _mikrotik_connection(network_device) as api:
        _remove_rules_by_comment(api, comment)

    logger.info("Internet desbloqueado para device_id=%s", device_id)


# Activa el bloqueo global de internet en el router
def global_block_internet(network_device, allowed_host=None):
    allowed = allowed_host or settings.MIKROTIK_ALLOWED_HOST

    with _mikrotik_connection(network_device) as api:
        # Elimina reglas globales previas para evitar duplicados
        _remove_rules_by_comment(api, COMMENT_GLOBAL_BLOCK)

        filt = _get_firewall_filter(api)
        first_rule_id = _get_first_forward_rule_id(api)

        # Reglas del bloqueo global insertadas al inicio del chain
        rules = [
            # Permite trafico hacia el host autorizado
            {
                "chain": "forward", "action": "accept",
                "dst-address": allowed,
                "comment": COMMENT_GLOBAL_BLOCK,
            },
            # Permite trafico desde el host autorizado
            {
                "chain": "forward", "action": "accept",
                "src-address": allowed,
                "comment": COMMENT_GLOBAL_BLOCK,
            },
            # Bloquea todo el trafico forward restante
            {
                "chain": "forward", "action": "drop",
                "comment": COMMENT_GLOBAL_BLOCK,
            },
        ]

        # Inserta todas las reglas al inicio del chain forward
        # para que prevalezcan sobre cualquier regla existente
        for rule_params in rules:
            if first_rule_id:
                rule_params["place-before"] = first_rule_id
            filt.add(**rule_params)

    logger.info(
        "Bloqueo global activado en router=%s (permitido: %s)",
        network_device.ip_address, allowed,
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
# Busca reglas con el comentario MONITOR_GLOBAL_BLOCK en el firewall
def is_global_block_active(network_device):
    with _mikrotik_connection(network_device) as api:
        filt = _get_firewall_filter(api)
        for rule in filt:
            if rule.get("comment", "") == COMMENT_GLOBAL_BLOCK:
                return True
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
