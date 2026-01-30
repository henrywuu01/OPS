from django.urls import path
from . import views

urlpatterns = [
    path('', views.DepartmentListCreateView.as_view(), name='department_list'),
    path('tree/', views.DepartmentTreeView.as_view(), name='department_tree'),
    path('<int:pk>/', views.DepartmentDetailView.as_view(), name='department_detail'),
]
