# ViewSets de la API REST para dispositivos aulas y equipos de red
import logging

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .consumers import agent_group_name
from .models import Device, Classroom, NetworkDevice
from .serializer import DeviceSerializer, ClassroomSerializer, NetworkDeviceSerializer, ClassRoomSimpleSerializer
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

# CRUD de equipos de red como switches y routers
class NetworkDevicViewSet(viewsets.ModelViewSet):
    queryset = NetworkDevice.objects.all()
    permission_classes = [StrictDjangoModelPermissions, IsAuthenticated]
    serializer_class = NetworkDeviceSerializer

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



