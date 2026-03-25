# Permisos personalizados para la aplicacion de dispositivos
from rest_framework import permissions


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


# Solo permite operaciones CRUD de escritura (create update destroy) a usuarios staff
# Las acciones personalizadas como toggle-internet o shutdown se permiten a todos
class IsStaffForWrite(permissions.BasePermission):
    # Acciones CRUD estandar que solo los staff pueden realizar
    STAFF_ONLY_ACTIONS = {'create', 'update', 'partial_update', 'destroy'}

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        # Solo restringe las acciones CRUD estandar a staff
        action = getattr(view, 'action', None)
        if action in self.STAFF_ONLY_ACTIONS:
            return request.user and request.user.is_staff
        return True