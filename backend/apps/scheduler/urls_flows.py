from django.urls import path
from . import views

urlpatterns = [
    # Flow CRUD
    path('', views.JobFlowListCreateView.as_view(), name='flow_list'),
    path('<int:pk>/', views.JobFlowDetailView.as_view(), name='flow_detail'),

    # Flow operations
    path('<int:pk>/trigger/', views.JobFlowTriggerView.as_view(), name='flow_trigger'),

    # Flow instances
    path('<int:pk>/instances/', views.FlowInstanceListView.as_view(), name='flow_instances'),
    path('<int:pk>/instances/<str:instance_id>/', views.FlowInstanceDetailView.as_view(), name='flow_instance_detail'),
]
