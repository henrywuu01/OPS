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
]
