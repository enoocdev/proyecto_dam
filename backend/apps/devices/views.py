from .models import Device, Classroom, NetworkDevice
from  rest_framework import viewsets
from rest_framework.permissions import IsAdminUser , IsAuthenticated, DjangoModelPermissions
from .serializer import DeviceSerializer, ClassroomSerializer, NetworkDeviceSerializer



class DevicesViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    serializer_class = DeviceSerializer

class NetworkDevicViewSet(viewsets.ModelViewSet):
    queryset = NetworkDevice.objects.all()
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    serializer_class = NetworkDeviceSerializer

class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = Classroom.objects.all()
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    serializer_class = ClassroomSerializer



