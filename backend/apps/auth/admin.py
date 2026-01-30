from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Department, Role, Permission, UserRole, RolePermission


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'real_name', 'department', 'is_active', 'is_staff']
    list_filter = ['is_active', 'is_staff', 'department']
    search_fields = ['username', 'email', 'real_name']
    ordering = ['-created_at']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('email', 'phone', 'real_name', 'avatar', 'department')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'data_scope')}),
        ('MFA', {'fields': ('mfa_enabled',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent', 'leader', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent', 'is_active', 'sort_order']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'module', 'type', 'is_active']
    list_filter = ['module', 'type', 'is_active']
    search_fields = ['name', 'code']


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'created_at']


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['role', 'permission', 'created_at']
