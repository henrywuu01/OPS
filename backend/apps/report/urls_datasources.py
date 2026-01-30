from django.urls import path
from . import views

urlpatterns = [
    path('', views.DataSourceListCreateView.as_view(), name='datasource_list'),
    path('<int:pk>/', views.DataSourceDetailView.as_view(), name='datasource_detail'),
    path('<int:pk>/test/', views.DataSourceTestView.as_view(), name='datasource_test'),
]
