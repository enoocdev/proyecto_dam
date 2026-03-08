# Permisos personalizados para la aplicacion de usuarios
from rest_framework import permissions

# Permite a los admin ver todo y a los usuarios normales solo su propio perfil
class IsOwnerOrAdmin(permissions.BasePermission):
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj == request.user
    

# Extiende DjangoModelPermissions para exigir permiso tambien en peticiones GET
class StrictDjangoModelPermissions(permissions.DjangoModelPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }