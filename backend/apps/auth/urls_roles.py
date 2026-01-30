from django.urls import path
from . import views

urlpatterns = [
    path('', views.RoleListCreateView.as_view(), name='role_list'),
    path('<int:pk>/', views.RoleDetailView.as_view(), name='role_detail'),
    path('<int:pk>/permissions/', views.RolePermissionsView.as_view(), name='role_permissions'),
    path('permissions/', views.PermissionListView.as_view(), name='permission_list'),
]
