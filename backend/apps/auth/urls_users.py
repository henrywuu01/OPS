from django.urls import path
from . import views

urlpatterns = [
    path('', views.UserListCreateView.as_view(), name='user_list'),
    path('<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('<int:pk>/status/', views.UserStatusView.as_view(), name='user_status'),
    path('<int:pk>/reset-password/', views.UserResetPasswordView.as_view(), name='user_reset_password'),
]
