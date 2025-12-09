from  rest_framework import viewsets
from rest_framework.permissions import IsAdminUser , IsAuthenticated
from ..users.permissions import IsOwnerOrAdmin, StrictDjangoModelPermissions
from .serializers import UserPermisionsSerializer, GroupSerializer, UserSerializer, CustomTokenObtainPairSerializer
from django.contrib.auth.models import Permission, Group
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView

User = get_user_model()
# Create your views here.

# backend/api/views.py



class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated,StrictDjangoModelPermissions, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=user.id)




class UserPermissionsView(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = UserPermisionsSerializer
    permission_classes = [StrictDjangoModelPermissions,IsAdminUser]

class UserGroupView(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [StrictDjangoModelPermissions,IsAdminUser]


