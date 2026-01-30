"""
RBAC Permission classes and decorators.
"""
from functools import wraps
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status


class RBACPermission(permissions.BasePermission):
    """
    RBAC permission class for DRF views.

    Usage:
        class MyView(APIView):
            permission_classes = [RBACPermission]
            required_permissions = ['user:read', 'user:write']
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superuser has all permissions
        if request.user.is_superuser:
            return True

        # Get required permissions from view
        required_permissions = getattr(view, 'required_permissions', [])

        if not required_permissions:
            return True

        # Get user permissions
        user_permissions = self._get_user_permissions(request.user)

        # Check if user has all required permissions
        for perm in required_permissions:
            if perm not in user_permissions and '*' not in user_permissions:
                return False

        return True

    def _get_user_permissions(self, user):
        """Get all permissions for a user through their roles."""
        permissions_set = set()

        for user_role in user.user_roles.select_related('role'):
            for rp in user_role.role.role_permissions.select_related('permission'):
                permissions_set.add(rp.permission.code)

        return permissions_set


class DataPermission(permissions.BasePermission):
    """
    Data-level permission class.

    Handles row-level permissions based on user's data_scope setting.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        data_scope = request.user.data_scope

        if data_scope == 'ALL':
            return True

        elif data_scope == 'DEPT':
            # Only own department data
            if hasattr(obj, 'department_id'):
                return obj.department_id == request.user.department_id
            if hasattr(obj, 'created_by'):
                return obj.created_by.department_id == request.user.department_id

        elif data_scope == 'DEPT_CHILD':
            # Own department and child departments
            if not request.user.department:
                return False
            dept_ids = [request.user.department_id]
            dept_ids.extend([d.id for d in request.user.department.get_descendants()])

            if hasattr(obj, 'department_id'):
                return obj.department_id in dept_ids
            if hasattr(obj, 'created_by'):
                return obj.created_by.department_id in dept_ids

        elif data_scope == 'SELF':
            # Only own data
            if hasattr(obj, 'created_by_id'):
                return obj.created_by_id == request.user.id
            if hasattr(obj, 'user_id'):
                return obj.user_id == request.user.id

        return False


def require_permission(*permissions):
    """
    Decorator for function-based views or methods requiring specific permissions.

    Usage:
        @require_permission('user:read')
        def my_view(request):
            ...

        @require_permission('user:read', 'user:write')
        def my_view(request):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            user = request.user

            if not user or not user.is_authenticated:
                return Response(
                    {'error': '请先登录'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            if user.is_superuser:
                return func(request, *args, **kwargs)

            # Get user permissions
            user_permissions = set()
            for user_role in user.user_roles.select_related('role'):
                for rp in user_role.role.role_permissions.select_related('permission'):
                    user_permissions.add(rp.permission.code)

            # Check permissions
            for perm in permissions:
                if perm not in user_permissions and '*' not in user_permissions:
                    return Response(
                        {'error': '没有操作权限'},
                        status=status.HTTP_403_FORBIDDEN
                    )

            return func(request, *args, **kwargs)
        return wrapper
    return decorator


class PermissionMixin:
    """
    Mixin for class-based views to check permissions.

    Usage:
        class MyView(PermissionMixin, APIView):
            permission_map = {
                'GET': ['user:read'],
                'POST': ['user:create'],
                'PUT': ['user:update'],
                'DELETE': ['user:delete'],
            }
    """

    permission_map = {}

    def get_required_permissions(self):
        """Get required permissions for the current request method."""
        return self.permission_map.get(self.request.method, [])

    def check_permissions(self, request):
        super().check_permissions(request)

        if request.user.is_superuser:
            return

        required_permissions = self.get_required_permissions()
        if not required_permissions:
            return

        user_permissions = set()
        for user_role in request.user.user_roles.select_related('role'):
            for rp in user_role.role.role_permissions.select_related('permission'):
                user_permissions.add(rp.permission.code)

        for perm in required_permissions:
            if perm not in user_permissions and '*' not in user_permissions:
                self.permission_denied(
                    request,
                    message='没有操作权限'
                )


def get_user_permissions(user) -> set:
    """
    Get all permission codes for a user.

    Args:
        user: User instance

    Returns:
        Set of permission codes
    """
    if not user or not user.is_authenticated:
        return set()

    if user.is_superuser:
        return {'*'}

    permissions_set = set()
    for user_role in user.user_roles.select_related('role'):
        for rp in user_role.role.role_permissions.select_related('permission'):
            permissions_set.add(rp.permission.code)

    return permissions_set


def has_permission(user, permission_code: str) -> bool:
    """
    Check if user has a specific permission.

    Args:
        user: User instance
        permission_code: Permission code to check

    Returns:
        True if user has the permission
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    user_permissions = get_user_permissions(user)
    return permission_code in user_permissions or '*' in user_permissions
