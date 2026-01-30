from django.urls import path
from . import views

urlpatterns = [
    # Job endpoints
    path('', views.JobListCreateView.as_view(), name='job_list_create'),
    path('statistics/', views.JobStatisticsView.as_view(), name='job_statistics'),
    path('<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('<int:pk>/trigger/', views.JobTriggerView.as_view(), name='job_trigger'),
    path('<int:pk>/pause/', views.JobPauseView.as_view(), name='job_pause'),
    path('<int:pk>/resume/', views.JobResumeView.as_view(), name='job_resume'),
    path('<int:pk>/logs/', views.JobLogListView.as_view(), name='job_logs'),
    path('<int:pk>/logs/<int:log_id>/', views.JobLogDetailView.as_view(), name='job_log_detail'),
]
