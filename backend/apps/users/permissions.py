from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permite que los admin vean todo.
    Permite que los usuarios normales solo vean o editen SU PROPIO perfil.
    """
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj == request.user