from  rest_framework import viewsets
from rest_framework.permissions import IsAdminUser , IsAuthenticated, DjangoModelPermissions
from ..users.permissions import IsOwnerOrAdmin
from .serializers import UserPermisionsSerializer, GroupSerializer, UserSerializer
from django.contrib.auth.models import Permission, Group
from django.contrib.auth import get_user_model

User = get_user_model()
# Create your views here.

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated,DjangoModelPermissions, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=user.id)




class UserPermissionsView(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = UserPermisionsSerializer
    permission_classes = [DjangoModelPermissions,IsAdminUser]

class UserGroupView(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [DjangoModelPermissions,IsAdminUser]


