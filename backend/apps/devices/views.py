# ViewSets de la API REST para dispositivos aulas y equipos de red
import logging
from datetime import datetime

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .consumers import agent_group_name, DASHBOARD_GROUP
from . import mikrotik_service
from .mikrotik_service import MikrotikError
from .models import Device, Classroom, NetworkDevice
from .serializer import (
    DeviceSerializer, ClassroomSerializer, NetworkDeviceSerializer,
    ClassRoomSimpleSerializer, BlockInternetSerializer,
)
from .permissions import StrictDjangoModelPermissions

logger = logging.getLogger("devices.views")


# CRUD de dispositivos con filtro opcional por aula
class DevicesViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    permission_classes = [StrictDjangoModelPermissions, IsAuthenticated ]
    serializer_class = DeviceSerializer
    pagination_class = None

    # Filtra los dispositivos por aula si se pasa el parametro en la URL
    def get_queryset(self):
        queryset = super().get_queryset()
        classroom_id = self.request.query_params.get('classroom')
        if classroom_id is not None:
            queryset = queryset.filter(classroom_id=classroom_id)
        return queryset

    # POST /devices/{id}/shutdown/
    # Envia la orden de apagado al agente conectado por WebSocket
    @action(detail=True, methods=["post"], url_path="shutdown")
    def shutdown(self, request, pk=None):
        device = self.get_object()

        if not device.is_online:
            return Response(
                {"detail": "El dispositivo no está encendido."},
                status=status.HTTP_409_CONFLICT,
            )

        group = agent_group_name(device.mac)
        channel_layer = get_channel_layer()

        # Envia el comando de apagado al grupo del agente a traves del channel layer
        async_to_sync(channel_layer.group_send)(
            group,
            {
                "type": "agent.command",
                "command": "shutdown",
                "params": {},
            },
        )

        logger.info(
            "Orden de apagado enviada a %s (mac=%s) por usuario %s",
            device.hostname, device.mac, request.user,
        )

        return Response(
            {"detail": f"Orden de apagado enviada a {device.hostname}."},
            status=status.HTTP_200_OK,
        )

    # POST /devices/{id}/toggle-internet/
    # Alterna el estado de internet del dispositivo en el router MikroTik
    # Si esta bloqueado lo desbloquea y viceversa
    @action(detail=True, methods=["post"], url_path="toggle-internet")
    def toggle_internet(self, request, pk=None):
        device = self.get_object()

        if not device.connected_device:
            return Response(
                {"detail": "El dispositivo no tiene un equipo de red asignado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Decide si bloquear o desbloquear segun el estado actual
        will_block = not device.is_internet_blocked

        try:
            if will_block:
                serializer = BlockInternetSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                allowed_host = serializer.validated_data.get("allowed_host")

                mikrotik_service.block_device_internet(
                    network_device=device.connected_device,
                    device_ip=str(device.ip),
                    device_id=device.id,
                    allowed_host=str(allowed_host) if allowed_host else None,
                )
            else:
                mikrotik_service.unblock_device_internet(
                    network_device=device.connected_device,
                    device_id=device.id,
                )
        except MikrotikError as e:
            logger.error(
                "Error MikroTik al %s internet device_id=%s: %s",
                "bloquear" if will_block else "desbloquear", device.id, e,
            )
            return Response(
                {"detail": str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        device.is_internet_blocked = will_block
        device.save()

        event = "internet_blocked" if will_block else "internet_unblocked"

        # Notifica al dashboard del cambio de estado del dispositivo
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            DASHBOARD_GROUP,
            {
                "type": "device.status",
                "payload": {
                    "event": event,
                    "device": {
                        "id": device.id,
                        "mac": device.mac,
                        "ip": str(device.ip),
                        "hostname": device.hostname,
                        "is_online": device.is_online,
                        "is_internet_blocked": device.is_internet_blocked,
                        "classroom_id": device.classroom_id,
                    },
                    "timestamp": datetime.now().isoformat(),
                },
            },
        )

        action_text = "bloqueado" if will_block else "desbloqueado"
        logger.info(
            "Internet %s para %s (mac=%s) por usuario %s",
            action_text, device.hostname, device.mac, request.user,
        )

        return Response(
            {"detail": f"Internet {action_text} para {device.hostname}."},
            status=status.HTTP_200_OK,
        )

# CRUD de equipos de red como switches y routers
# Incluye acciones para gestionar el bloqueo global de internet
class NetworkDevicViewSet(viewsets.ModelViewSet):
    queryset = NetworkDevice.objects.all()
    permission_classes = [StrictDjangoModelPermissions, IsAuthenticated]
    serializer_class = NetworkDeviceSerializer

    # POST /network-device/{id}/toggle-global-internet/
    # Alterna el bloqueo global de internet en el router
    @action(detail=True, methods=["post"], url_path="toggle-global-internet")
    def toggle_global_internet(self, request, pk=None):
        network_device = self.get_object()

        # Comprueba si ya existe un bloqueo global activo en el router
        will_block = not mikrotik_service.is_global_block_active(network_device)

        try:
            if will_block:
                serializer = BlockInternetSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                allowed_host = serializer.validated_data.get("allowed_host")

                mikrotik_service.global_block_internet(
                    network_device=network_device,
                    allowed_host=str(allowed_host) if allowed_host else None,
                )
            else:
                mikrotik_service.global_unblock_internet(
                    network_device=network_device,
                )
        except MikrotikError as e:
            logger.error(
                "Error MikroTik al %s bloqueo global en %s: %s",
                "activar" if will_block else "desactivar",
                network_device.ip_address, e,
            )
            return Response(
                {"detail": str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        event = "global_block" if will_block else "global_unblock"

        # Notifica al dashboard del cambio de bloqueo global
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            DASHBOARD_GROUP,
            {
                "type": "device.status",
                "payload": {
                    "event": event,
                    "network_device_id": network_device.id,
                    "timestamp": datetime.now().isoformat(),
                },
            },
        )

        action_text = "activado" if will_block else "desactivado"
        logger.info(
            "Bloqueo global %s en %s por usuario %s",
            action_text, network_device.ip_address, request.user,
        )

        return Response(
            {"detail": f"Bloqueo global de internet {action_text}."},
            status=status.HTTP_200_OK,
        )

# CRUD de aulas con paginacion
class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = Classroom.objects.all().order_by("id")
    permission_classes = [StrictDjangoModelPermissions, IsAuthenticated ]
    serializer_class = ClassroomSerializer

# Listado de aulas de solo lectura sin paginacion para selectores del frontend
class ReadOnlyClassRoomWithoutPagination(viewsets.ReadOnlyModelViewSet):
    queryset = Classroom.objects.all().order_by("id")
    serializer_class = ClassRoomSimpleSerializer
    permission_classes = [StrictDjangoModelPermissions, IsAuthenticated]
    pagination_class = None



