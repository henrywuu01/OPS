from django.urls import path
from . import views

urlpatterns = [
    # Job endpoints
    path('jobs/', views.JobListCreateView.as_view(), name='job_list_create'),
    path('jobs/<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('jobs/<int:pk>/trigger/', views.JobTriggerView.as_view(), name='job_trigger'),
    path('jobs/<int:pk>/pause/', views.JobPauseView.as_view(), name='job_pause'),
    path('jobs/<int:pk>/resume/', views.JobResumeView.as_view(), name='job_resume'),
    path('jobs/<int:pk>/logs/', views.JobLogListView.as_view(), name='job_logs'),
    path('jobs/<int:pk>/logs/<int:log_id>/', views.JobLogDetailView.as_view(), name='job_log_detail'),

    # Job flow endpoints
    path('job-flows/', views.JobFlowListCreateView.as_view(), name='job_flow_list_create'),
    path('job-flows/<int:pk>/', views.JobFlowDetailView.as_view(), name='job_flow_detail'),
    path('job-flows/<int:pk>/trigger/', views.JobFlowTriggerView.as_view(), name='job_flow_trigger'),
]
