"""
User authentication models.
"""
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from simple_history.models import HistoricalRecords


class UserManager(BaseUserManager):
    """Custom user manager."""

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('用户名不能为空')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model."""

    class Meta:
        db_table = 't_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    # Override PermissionsMixin fields to avoid clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )

    username = models.CharField('用户名', max_length=50, unique=True)
    email = models.EmailField('邮箱', max_length=100, blank=True, null=True)
    phone = models.CharField('手机号', max_length=20, blank=True, null=True)
    real_name = models.CharField('真实姓名', max_length=50, blank=True, null=True)
    avatar = models.URLField('头像', max_length=500, blank=True, null=True)
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='部门'
    )

    # Status
    is_active = models.BooleanField('是否激活', default=True)
    is_staff = models.BooleanField('是否管理员', default=False)

    # MFA
    mfa_secret = models.CharField('MFA密钥', max_length=100, blank=True, null=True)
    mfa_enabled = models.BooleanField('是否开启MFA', default=False)

    # Data scope
    DATA_SCOPE_CHOICES = [
        ('ALL', '全部数据'),
        ('DEPT', '本部门数据'),
        ('DEPT_CHILD', '本部门及子部门'),
        ('SELF', '仅本人数据'),
        ('CUSTOM', '自定义'),
    ]
    data_scope = models.CharField('数据权限', max_length=20, choices=DATA_SCOPE_CHOICES, default='SELF')

    # Login info
    last_login_ip = models.GenericIPAddressField('最后登录IP', blank=True, null=True)
    login_count = models.IntegerField('登录次数', default=0)
    login_failed_count = models.IntegerField('连续登录失败次数', default=0)
    locked_until = models.DateTimeField('锁定至', blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    # History
    history = HistoricalRecords()

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username

    def get_full_name(self):
        return self.real_name or self.username

    def get_short_name(self):
        return self.username


class Department(models.Model):
    """Department model."""

    class Meta:
        db_table = 't_department'
        verbose_name = '部门'
        verbose_name_plural = verbose_name

    name = models.CharField('部门名称', max_length=100)
    code = models.CharField('部门编码', max_length=50, unique=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='上级部门'
    )
    leader = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_departments',
        verbose_name='部门负责人'
    )
    sort_order = models.IntegerField('排序', default=0)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    def __str__(self):
        return self.name

    def get_ancestors(self):
        """Get all ancestor departments."""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors

    def get_descendants(self):
        """Get all descendant departments."""
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants


class Role(models.Model):
    """Role model."""

    class Meta:
        db_table = 't_role'
        verbose_name = '角色'
        verbose_name_plural = verbose_name

    name = models.CharField('角色名称', max_length=50, unique=True)
    code = models.CharField('角色编码', max_length=50, unique=True)
    description = models.TextField('描述', blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='上级角色'
    )
    is_active = models.BooleanField('是否启用', default=True)
    sort_order = models.IntegerField('排序', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    def __str__(self):
        return self.name


class Permission(models.Model):
    """Permission model."""

    class Meta:
        db_table = 't_permission'
        verbose_name = '权限'
        verbose_name_plural = verbose_name
        unique_together = ['module', 'code']

    TYPE_CHOICES = [
        ('menu', '菜单'),
        ('button', '按钮'),
        ('api', '接口'),
    ]

    name = models.CharField('权限名称', max_length=100)
    code = models.CharField('权限编码', max_length=100)
    module = models.CharField('所属模块', max_length=50)
    type = models.CharField('权限类型', max_length=20, choices=TYPE_CHOICES, default='api')
    path = models.CharField('路由/接口路径', max_length=200, blank=True, null=True)
    method = models.CharField('请求方法', max_length=20, blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='上级权限'
    )
    sort_order = models.IntegerField('排序', default=0)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    def __str__(self):
        return f'{self.module}:{self.name}'


class UserRole(models.Model):
    """User-Role relationship."""

    class Meta:
        db_table = 't_user_role'
        verbose_name = '用户角色'
        verbose_name_plural = verbose_name
        unique_together = ['user', 'role']

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_users')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)


class RolePermission(models.Model):
    """Role-Permission relationship."""

    class Meta:
        db_table = 't_role_permission'
        verbose_name = '角色权限'
        verbose_name_plural = verbose_name
        unique_together = ['role', 'permission']

    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='permission_roles')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
