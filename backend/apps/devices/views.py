from .models import Device, Classroom, NetworkDevice
from  rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializer import DeviceSerializer, ClassroomSerializer, NetworkDeviceSerializer, DeviceSimpleSerializer
from .permissions import StrictDjangoModelPermissions



class DevicesViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    permission_classes = [StrictDjangoModelPermissions, IsAuthenticated ]
    serializer_class = DeviceSerializer
    pagination_class = None

class NetworkDevicViewSet(viewsets.ModelViewSet):
    queryset = NetworkDevice.objects.all()
    permission_classes = [StrictDjangoModelPermissions, IsAuthenticated]
    serializer_class = NetworkDeviceSerializer

class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = Classroom.objects.all().order_by("id")
    permission_classes = [StrictDjangoModelPermissions, IsAuthenticated ]
    serializer_class = ClassroomSerializer

class ReadOnlyDeviceWithoutPagination(viewsets.ReadOnlyModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSimpleSerializer
    permission_classes = [StrictDjangoModelPermissions, IsAuthenticated]
    pagination_class = None



