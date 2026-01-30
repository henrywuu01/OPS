"""
Authentication views - placeholder for M0.
Views will be fully implemented in M1.
"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenRefreshView as JWTTokenRefreshView


class LoginView(APIView):
    """User login view - to be implemented in M1."""
    permission_classes = [AllowAny]

    def post(self, request):
        return Response({'message': 'Login endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class LogoutView(APIView):
    """User logout view - to be implemented in M1."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({'message': 'Logout endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class TokenRefreshView(JWTTokenRefreshView):
    """Token refresh view."""
    pass


class PasswordChangeView(APIView):
    """Password change view - to be implemented in M1."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({'message': 'Password change endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class PasswordResetView(APIView):
    """Password reset view - to be implemented in M1."""
    permission_classes = [AllowAny]

    def post(self, request):
        return Response({'message': 'Password reset endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class ProfileView(APIView):
    """User profile view - to be implemented in M1."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'Profile endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def put(self, request):
        return Response({'message': 'Profile update endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class MFABindView(APIView):
    """MFA bind view - to be implemented in M1."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({'message': 'MFA bind endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class MFAVerifyView(APIView):
    """MFA verify view - to be implemented in M1."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({'message': 'MFA verify endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class UserListCreateView(APIView):
    """User list and create view - to be implemented in M1."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'User list endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def post(self, request):
        return Response({'message': 'User create endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class UserDetailView(APIView):
    """User detail view - to be implemented in M1."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        return Response({'message': 'User detail endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def put(self, request, pk):
        return Response({'message': 'User update endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def delete(self, request, pk):
        return Response({'message': 'User delete endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class UserStatusView(APIView):
    """User status view - to be implemented in M1."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'User status endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class UserResetPasswordView(APIView):
    """User reset password view - to be implemented in M1."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        return Response({'message': 'User reset password endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class RoleListCreateView(APIView):
    """Role list and create view - to be implemented in M1."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'Role list endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def post(self, request):
        return Response({'message': 'Role create endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class RoleDetailView(APIView):
    """Role detail view - to be implemented in M1."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        return Response({'message': 'Role detail endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def put(self, request, pk):
        return Response({'message': 'Role update endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def delete(self, request, pk):
        return Response({'message': 'Role delete endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class RolePermissionsView(APIView):
    """Role permissions view - to be implemented in M1."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        return Response({'message': 'Role permissions endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)

    def put(self, request, pk):
        return Response({'message': 'Role permissions update endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)


class PermissionListView(APIView):
    """Permission list view - to be implemented in M1."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': 'Permission list endpoint - M1'}, status=status.HTTP_501_NOT_IMPLEMENTED)
