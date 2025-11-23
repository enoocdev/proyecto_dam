from .models import Device, Group
from  rest_framework import viewsets, permissions
from .serializer import DeviceSerializer, GroupSerializer
# Create your views here.

class DevicesViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = DeviceSerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = GroupSerializer

