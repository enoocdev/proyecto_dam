from  rest_framework import viewsets
from rest_framework.permissions import IsAdminUser , IsAuthenticated, DjangoModelPermissions
from ..users.permissions import IsOwnerOrAdmin, StrictDjangoModelPermissions
from .serializers import UserPermisionsSerializer, GroupSerializer, UserSerializer, CustomTokenObtainPairSerializer,GroupSimpleSerializer
from django.contrib.auth.models import Permission, Group
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView

User = get_user_model()
# Create your views here.

# backend/api/views.py



class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin , DjangoModelPermissions]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=user.id)




class UserPermissionsView(viewsets.ReadOnlyModelViewSet):
    # queryset = Permission.objects.all()
    serializer_class = UserPermisionsSerializer
    permission_classes = [StrictDjangoModelPermissions, IsAdminUser]
    pagination_class = None

    # queryset filtrado para que no muestre permisos no necesarios como los permisos de sesiones ...
    def get_queryset(self):
        return Permission.objects.filter(
            content_type__app_label__in=[
            'users',
            'devices',
            'auth',
        ]  
        ).order_by('id')

class UserGroupView(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by('id')
    serializer_class = GroupSerializer
    permission_classes = [StrictDjangoModelPermissions, IsAdminUser]

class ReadOnlyGroupWithoutPagination(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSimpleSerializer
    permission_classes = [StrictDjangoModelPermissions, IsAdminUser]
    pagination_class = None


