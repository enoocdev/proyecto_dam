from .models import Device, DeviceGroup
from  rest_framework import viewsets
from rest_framework.permissions import IsAdminUser , IsAuthenticated, DjangoModelPermissions
from .serializer import DeviceSerializer, DeviceGroupSerializer, UserSerializer, UserGroupSerializer
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

User = get_user_model()
# Create your views here.

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

class UserGoupView(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = UserGroupSerializer
    permission_classes = [IsAdminUser]




class DevicesViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    serializer_class = DeviceSerializer


class DeviceGroupViewSet(viewsets.ModelViewSet):
    queryset = DeviceGroup.objects.all()
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    serializer_class = DeviceGroupSerializer

