"""
Authentication serializers.
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Department, Role, Permission, UserRole, RolePermission


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer with additional user info."""

    def validate(self, attrs):
        data = super().validate(attrs)

        # Add extra user info
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'real_name': self.user.real_name,
            'email': self.user.email,
            'avatar': self.user.avatar,
            'is_staff': self.user.is_staff,
        }

        # Update login count
        self.user.login_count += 1
        self.user.login_failed_count = 0
        self.user.save(update_fields=['login_count', 'login_failed_count'])

        return data


class LoginSerializer(serializers.Serializer):
    """Login request serializer."""
    username = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=128, write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(username=username, password=password)

        if not user:
            # Check if user exists and increment failed count
            try:
                existing_user = User.objects.get(username=username)
                existing_user.login_failed_count += 1
                existing_user.save(update_fields=['login_failed_count'])

                if existing_user.login_failed_count >= 5:
                    raise serializers.ValidationError('账号已被锁定，请联系管理员')
            except User.DoesNotExist:
                pass

            raise serializers.ValidationError('用户名或密码错误')

        if not user.is_active:
            raise serializers.ValidationError('账号已被禁用')

        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """User serializer."""
    department_name = serializers.CharField(source='department.name', read_only=True)
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'real_name', 'avatar',
            'department', 'department_name', 'is_active', 'is_staff',
            'data_scope', 'mfa_enabled', 'login_count', 'last_login',
            'created_at', 'updated_at', 'roles'
        ]
        read_only_fields = ['login_count', 'last_login', 'created_at', 'updated_at']

    def get_roles(self, obj):
        return list(obj.user_roles.values_list('role__name', flat=True))


class UserCreateSerializer(serializers.ModelSerializer):
    """User creation serializer."""
    password = serializers.CharField(write_only=True, required=True)
    role_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        default=[]
    )

    class Meta:
        model = User
        fields = [
            'username', 'password', 'email', 'phone', 'real_name',
            'avatar', 'department', 'is_active', 'is_staff', 'data_scope',
            'role_ids'
        ]

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        role_ids = validated_data.pop('role_ids', [])
        password = validated_data.pop('password')

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        # Assign roles
        for role_id in role_ids:
            UserRole.objects.create(user=user, role_id=role_id)

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """User update serializer."""
    role_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = User
        fields = [
            'email', 'phone', 'real_name', 'avatar', 'department',
            'is_active', 'is_staff', 'data_scope', 'role_ids'
        ]

    def update(self, instance, validated_data):
        role_ids = validated_data.pop('role_ids', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update roles if provided
        if role_ids is not None:
            instance.user_roles.all().delete()
            for role_id in role_ids:
                UserRole.objects.create(user=instance, role_id=role_id)

        return instance


class PasswordChangeSerializer(serializers.Serializer):
    """Password change serializer."""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('原密码错误')
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value


class ProfileSerializer(serializers.ModelSerializer):
    """User profile serializer."""
    department_name = serializers.CharField(source='department.name', read_only=True)
    roles = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'real_name', 'avatar',
            'department', 'department_name', 'is_staff', 'data_scope',
            'mfa_enabled', 'roles', 'permissions'
        ]
        read_only_fields = ['username', 'is_staff']

    def get_roles(self, obj):
        return list(obj.user_roles.values_list('role__code', flat=True))

    def get_permissions(self, obj):
        if obj.is_superuser:
            return ['*']

        permissions = set()
        for user_role in obj.user_roles.select_related('role'):
            for rp in user_role.role.role_permissions.select_related('permission'):
                permissions.add(rp.permission.code)
        return list(permissions)


class DepartmentSerializer(serializers.ModelSerializer):
    """Department serializer."""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    leader_name = serializers.CharField(source='leader.real_name', read_only=True)

    class Meta:
        model = Department
        fields = [
            'id', 'name', 'code', 'parent', 'parent_name',
            'leader', 'leader_name', 'sort_order', 'is_active',
            'created_at', 'updated_at'
        ]


class RoleSerializer(serializers.ModelSerializer):
    """Role serializer."""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = [
            'id', 'name', 'code', 'description', 'parent', 'parent_name',
            'is_active', 'sort_order', 'created_at', 'updated_at', 'permissions'
        ]

    def get_permissions(self, obj):
        return list(obj.role_permissions.values_list('permission_id', flat=True))


class RoleCreateUpdateSerializer(serializers.ModelSerializer):
    """Role create/update serializer."""
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        default=[]
    )

    class Meta:
        model = Role
        fields = [
            'name', 'code', 'description', 'parent',
            'is_active', 'sort_order', 'permission_ids'
        ]

    def create(self, validated_data):
        permission_ids = validated_data.pop('permission_ids', [])
        role = Role.objects.create(**validated_data)

        for perm_id in permission_ids:
            RolePermission.objects.create(role=role, permission_id=perm_id)

        return role

    def update(self, instance, validated_data):
        permission_ids = validated_data.pop('permission_ids', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if permission_ids is not None:
            instance.role_permissions.all().delete()
            for perm_id in permission_ids:
                RolePermission.objects.create(role=instance, permission_id=perm_id)

        return instance


class PermissionSerializer(serializers.ModelSerializer):
    """Permission serializer."""

    class Meta:
        model = Permission
        fields = [
            'id', 'name', 'code', 'module', 'type', 'path', 'method',
            'parent', 'sort_order', 'is_active'
        ]


class PermissionTreeSerializer(serializers.ModelSerializer):
    """Permission tree serializer."""
    children = serializers.SerializerMethodField()

    class Meta:
        model = Permission
        fields = ['id', 'name', 'code', 'module', 'type', 'children']

    def get_children(self, obj):
        children = obj.children.filter(is_active=True).order_by('sort_order')
        return PermissionTreeSerializer(children, many=True).data
