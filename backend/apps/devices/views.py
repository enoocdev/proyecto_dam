from .models import Device, DeviceGroup
from  rest_framework import viewsets
from rest_framework.permissions import IsAdminUser , IsAuthenticated, DjangoModelPermissions
from .serializer import DeviceSerializer, DeviceGroupSerializer



class DevicesViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    serializer_class = DeviceSerializer


class DeviceGroupViewSet(viewsets.ModelViewSet):
    queryset = DeviceGroup.objects.all()
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    serializer_class = DeviceGroupSerializer

