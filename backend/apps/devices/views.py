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
from librouteros.exceptions import TrapError
from .models import Device, Classroom, NetworkDevice, AllowedHost
from .serializer import (
    DeviceSerializer, ClassroomSerializer, NetworkDeviceSerializer,
    ClassRoomSimpleSerializer, AllowedHostSerializer,
)
from .permissions import StrictDjangoModelPermissions, IsStaffForWrite

logger = logging.getLogger("devices.views")


# CRUD de dispositivos con filtro opcional por aula
# Los usuarios no staff solo ven dispositivos de sus aulas asignadas
class DevicesViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    permission_classes = [StrictDjangoModelPermissions, IsAuthenticated ]
    serializer_class = DeviceSerializer
    pagination_class = None

    # Filtra los dispositivos por aula y por las aulas asignadas al usuario
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Los usuarios no staff solo ven dispositivos de sus aulas asignadas
        if not user.is_staff:
            queryset = queryset.filter(classroom__in=user.classrooms.all())

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
    # El bloqueo se aplica por PUERTO FISICO no por IP
    @action(detail=True, methods=["post"], url_path="toggle-internet")
    def toggle_internet(self, request, pk=None):
        device = self.get_object()

        if not device.connected_device:
            return Response(
                {"detail": "El dispositivo no tiene un equipo de red asignado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not device.switch_port or device.switch_port.strip() == "":
            return Response(
                {"detail": "El dispositivo no tiene un puerto de red asignado. Espere a que se detecte automaticamente."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Decide si bloquear o desbloquear segun el estado actual
        will_block = not device.is_internet_blocked

        try:
            if will_block:
                mikrotik_service.block_device_internet(
                    network_device=device.connected_device,
                    switch_port=device.switch_port,
                    device_id=device.id,
                )
            else:
                mikrotik_service.unblock_device_internet(
                    network_device=device.connected_device,
                    device_id=device.id,
                )
        except (MikrotikError, TrapError) as e:
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
                        "connected_device_id": device.connected_device_id,
                        "switch_port": device.switch_port,
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
# Solo accesible para usuarios staff ya que es configuracion de infraestructura
class NetworkDevicViewSet(viewsets.ModelViewSet):
    queryset = NetworkDevice.objects.all()
    permission_classes = [StrictDjangoModelPermissions, IsAuthenticated, IsStaffForWrite]
    serializer_class = NetworkDeviceSerializer

# CRUD de aulas con paginacion
# Incluye accion para gestionar el bloqueo de internet por aula
# Los usuarios no staff solo ven sus aulas asignadas y no pueden crear ni modificar aulas
class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = Classroom.objects.all().order_by("id")
    permission_classes = [StrictDjangoModelPermissions, IsAuthenticated, IsStaffForWrite]
    serializer_class = ClassroomSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_staff:
            queryset = queryset.filter(users=user)
        return queryset

    # POST /classroom/{id}/toggle-global-internet/
    # Alterna el bloqueo de internet para todos los dispositivos del aula
    @action(detail=True, methods=["post"], url_path="toggle-global-internet")
    def toggle_global_internet(self, request, pk=None):
        classroom = self.get_object()

        # Decide si bloquear o desbloquear segun el estado actual del aula
        will_block = not classroom.is_internet_blocked

        try:
            if will_block:
                mikrotik_service.classroom_block_internet(
                    classroom_id=classroom.id,
                )
            else:
                mikrotik_service.classroom_unblock_internet(
                    classroom_id=classroom.id,
                )
        except (MikrotikError, TrapError) as e:
            logger.error(
                "Error MikroTik al %s internet del aula %s: %s",
                "bloquear" if will_block else "desbloquear",
                classroom.name, e,
            )
            return Response(
                {"detail": str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        classroom.is_internet_blocked = will_block
        classroom.save()

        # Actualiza tambien el estado de cada dispositivo del aula
        classroom.device_set.update(is_internet_blocked=will_block)

        event = "classroom_block" if will_block else "classroom_unblock"

        # Notifica al dashboard del cambio de bloqueo del aula
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            DASHBOARD_GROUP,
            {
                "type": "device.status",
                "payload": {
                    "event": event,
                    "classroom_id": classroom.id,
                    "is_internet_blocked": will_block,
                    "timestamp": datetime.now().isoformat(),
                },
            },
        )

        action_text = "bloqueado" if will_block else "desbloqueado"
        logger.info(
            "Internet %s para aula %s por usuario %s",
            action_text, classroom.name, request.user,
        )

        return Response(
            {"detail": f"Internet {action_text} para el aula {classroom.name}."},
            status=status.HTTP_200_OK,
        )

# Listado de aulas de solo lectura sin paginacion para selectores del frontend
# Los usuarios no staff solo ven sus aulas asignadas
class ReadOnlyClassRoomWithoutPagination(viewsets.ReadOnlyModelViewSet):
    queryset = Classroom.objects.all().order_by("id")
    serializer_class = ClassRoomSimpleSerializer
    permission_classes = [StrictDjangoModelPermissions, IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_staff:
            queryset = queryset.filter(users=user)
        return queryset


# CRUD de hosts permitidos que no se aislaran al cortar internet
# Estos hosts seran accesibles incluso cuando un puerto este bloqueado
# Solo accesible para usuarios staff ya que es configuracion de infraestructura
class AllowedHostViewSet(viewsets.ModelViewSet):
    queryset = AllowedHost.objects.all().order_by("id")
    permission_classes = [StrictDjangoModelPermissions, IsAuthenticated, IsStaffForWrite]
    serializer_class = AllowedHostSerializer
    pagination_class = None



