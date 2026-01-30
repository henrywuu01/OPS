from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('password/reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('profile/', views.ProfileView.as_view(), name='profile'),

    # MFA
    path('mfa/bind/', views.MFABindView.as_view(), name='mfa_bind'),
    path('mfa/verify/', views.MFAVerifyView.as_view(), name='mfa_verify'),

    # SSO
    path('sso/config/', views.SSOConfigView.as_view(), name='sso_config'),
    path('sso/<str:provider>/login/', views.SSOLoginView.as_view(), name='sso_login'),
    path('sso/<str:provider>/callback/', views.SSOCallbackView.as_view(), name='sso_callback'),
    path('sso/<str:provider>/bind/', views.SSOBindView.as_view(), name='sso_bind'),
    path('sso/<str:provider>/unbind/', views.SSOUnbindView.as_view(), name='sso_unbind'),

    # User Management
    path('users/', views.UserListCreateView.as_view(), name='user_list_create'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/status/', views.UserStatusView.as_view(), name='user_status'),
    path('users/<int:pk>/reset-password/', views.UserResetPasswordView.as_view(), name='user_reset_password'),

    # Department Management
    path('departments/', views.DepartmentListCreateView.as_view(), name='department_list_create'),
    path('departments/tree/', views.DepartmentTreeView.as_view(), name='department_tree'),
    path('departments/<int:pk>/', views.DepartmentDetailView.as_view(), name='department_detail'),

    # Role Management
    path('roles/', views.RoleListCreateView.as_view(), name='role_list_create'),
    path('roles/<int:pk>/', views.RoleDetailView.as_view(), name='role_detail'),
    path('roles/<int:pk>/permissions/', views.RolePermissionsView.as_view(), name='role_permissions'),

    # Permission Management
    path('permissions/', views.PermissionListView.as_view(), name='permission_list'),
    path('permissions/tree/', views.PermissionTreeView.as_view(), name='permission_tree'),
]
