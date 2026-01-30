"""
Authentication views for M1 - Login Authentication Center.
"""
import pyotp
import qrcode
import base64
from io import BytesIO
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenRefreshView as JWTTokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
from django.contrib.auth import get_user_model

from .models import User, Department, Role, Permission, UserRole, RolePermission
from .serializers import (
    LoginSerializer, RegisterSerializer, UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    PasswordChangeSerializer, ProfileSerializer, DepartmentSerializer,
    RoleSerializer, RoleCreateUpdateSerializer, PermissionSerializer,
    PermissionTreeSerializer, CustomTokenObtainPairSerializer
)


class LoginView(APIView):
    """User login view with JWT token generation."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Update login count
        user.login_count += 1
        user.login_failed_count = 0
        user.save(update_fields=['login_count', 'login_failed_count'])

        # Return tokens with user info
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'real_name': user.real_name,
                'email': user.email,
                'avatar': user.avatar,
                'is_staff': user.is_staff,
            }
        })


class RegisterView(APIView):
    """User registration view."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens for auto-login after registration
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': '注册成功',
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'real_name': user.real_name,
                'email': user.email,
            }
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    """User logout view - blacklist refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': '退出成功'})
        except Exception:
            return Response({'message': '退出成功'})


class TokenRefreshView(JWTTokenRefreshView):
    """Token refresh view."""
    pass


class PasswordChangeView(APIView):
    """Password change view for authenticated users."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({'message': '密码修改成功'})


class PasswordResetView(APIView):
    """Password reset view - send reset email (placeholder)."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': '请提供邮箱地址'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
            # TODO: Send reset email via notification module
            return Response({'message': '重置邮件已发送，请查收'})
        except User.DoesNotExist:
            # Don't reveal if email exists
            return Response({'message': '重置邮件已发送，请查收'})


class ProfileView(APIView):
    """User profile view and update."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = ProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class MFABindView(APIView):
    """MFA bind view - generate TOTP secret and QR code."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Generate new secret
        secret = pyotp.random_base32()
        user.mfa_secret = secret
        user.save(update_fields=['mfa_secret'])

        # Generate OTP URI
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(
            name=user.username,
            issuer_name='OPS System'
        )

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')

        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return Response({
            'secret': secret,
            'qr_code': f'data:image/png;base64,{qr_base64}'
        })


class MFAVerifyView(APIView):
    """MFA verify view - verify TOTP code and enable MFA."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        code = request.data.get('code')

        if not code:
            return Response(
                {'error': '请提供验证码'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.mfa_secret:
            return Response(
                {'error': '请先绑定MFA'},
                status=status.HTTP_400_BAD_REQUEST
            )

        totp = pyotp.TOTP(user.mfa_secret)
        if totp.verify(code):
            user.mfa_enabled = True
            user.save(update_fields=['mfa_enabled'])
            return Response({'message': 'MFA验证成功'})
        else:
            return Response(
                {'error': '验证码错误'},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserListCreateView(generics.ListCreateAPIView):
    """User list and create view."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.all().order_by('-created_at')

        # Search filter
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(real_name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )

        # Department filter
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department_id=department)

        # Status filter
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        users = queryset[start:end]
        serializer = UserSerializer(users, many=True)

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """User detail, update and delete view."""
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Soft delete by deactivating
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserStatusView(APIView):
    """Toggle user active status."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            user.is_active = not user.is_active
            user.save(update_fields=['is_active'])
            return Response({
                'message': '用户状态更新成功',
                'is_active': user.is_active
            })
        except User.DoesNotExist:
            return Response(
                {'error': '用户不存在'},
                status=status.HTTP_404_NOT_FOUND
            )


class UserResetPasswordView(APIView):
    """Admin reset user password."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            new_password = request.data.get('password', 'Password123!')
            user.set_password(new_password)
            user.login_failed_count = 0
            user.save(update_fields=['password', 'login_failed_count'])
            return Response({'message': '密码重置成功'})
        except User.DoesNotExist:
            return Response(
                {'error': '用户不存在'},
                status=status.HTTP_404_NOT_FOUND
            )


class DepartmentListCreateView(generics.ListCreateAPIView):
    """Department list and create view."""
    permission_classes = [IsAuthenticated]
    queryset = Department.objects.all().order_by('sort_order')
    serializer_class = DepartmentSerializer


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Department detail view."""
    permission_classes = [IsAuthenticated]
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class DepartmentTreeView(APIView):
    """Get department tree structure."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        def build_tree(parent_id=None):
            nodes = []
            departments = Department.objects.filter(
                parent_id=parent_id,
                is_active=True
            ).order_by('sort_order')

            for dept in departments:
                node = {
                    'id': dept.id,
                    'name': dept.name,
                    'code': dept.code,
                    'leader_id': dept.leader_id,
                    'children': build_tree(dept.id)
                }
                nodes.append(node)
            return nodes

        tree = build_tree()
        return Response(tree)


class RoleListCreateView(generics.ListCreateAPIView):
    """Role list and create view."""
    permission_classes = [IsAuthenticated]
    queryset = Role.objects.all().order_by('sort_order')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RoleCreateUpdateSerializer
        return RoleSerializer


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Role detail view."""
    permission_classes = [IsAuthenticated]
    queryset = Role.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return RoleCreateUpdateSerializer
        return RoleSerializer


class RolePermissionsView(APIView):
    """Get and set role permissions."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            role = Role.objects.get(pk=pk)
            permission_ids = list(
                role.role_permissions.values_list('permission_id', flat=True)
            )
            return Response({'permissions': permission_ids})
        except Role.DoesNotExist:
            return Response(
                {'error': '角色不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, pk):
        try:
            role = Role.objects.get(pk=pk)
            permission_ids = request.data.get('permissions', [])

            # Clear existing permissions
            role.role_permissions.all().delete()

            # Add new permissions
            for perm_id in permission_ids:
                RolePermission.objects.create(role=role, permission_id=perm_id)

            return Response({'message': '权限更新成功'})
        except Role.DoesNotExist:
            return Response(
                {'error': '角色不存在'},
                status=status.HTTP_404_NOT_FOUND
            )


class PermissionListView(generics.ListAPIView):
    """Permission list view."""
    permission_classes = [IsAuthenticated]
    queryset = Permission.objects.filter(is_active=True).order_by('module', 'sort_order')
    serializer_class = PermissionSerializer


class PermissionTreeView(APIView):
    """Get permission tree structure."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        root_permissions = Permission.objects.filter(
            parent__isnull=True,
            is_active=True
        ).order_by('sort_order')
        serializer = PermissionTreeSerializer(root_permissions, many=True)
        return Response(serializer.data)
