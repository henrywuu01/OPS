from django.urls import path
from . import views

urlpatterns = [
    path('', views.JobFlowListCreateView.as_view(), name='flow_list'),
    path('<int:pk>/', views.JobFlowDetailView.as_view(), name='flow_detail'),
    path('<int:pk>/trigger/', views.JobFlowTriggerView.as_view(), name='flow_trigger'),
]
