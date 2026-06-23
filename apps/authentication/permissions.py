from rest_framework import permissions

class IsSuperAdmin(permissions.BasePermission):
    """
    Allows access only to users in the 'Super Admin' group.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.groups.filter(name='Super Admin').exists()

class IsAdminOrSuperAdmin(permissions.BasePermission):
    """
    Allows access to users in 'Admin' or 'Super Admin' groups.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.groups.filter(name__in=['Admin', 'Super Admin']).exists()
