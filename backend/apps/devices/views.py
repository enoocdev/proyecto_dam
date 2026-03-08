# ViewSets de la API REST para dispositivos aulas y equipos de red
from .models import Device, Classroom, NetworkDevice
from  rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializer import DeviceSerializer, ClassroomSerializer, NetworkDeviceSerializer, ClassRoomSimpleSerializer
from .permissions import StrictDjangoModelPermissions


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



