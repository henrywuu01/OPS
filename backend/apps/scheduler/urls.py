from django.urls import path
from . import views

urlpatterns = [
    # Job CRUD
    path('', views.JobListCreateView.as_view(), name='job_list_create'),
    path('<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),

    # Job operations
    path('<int:pk>/trigger/', views.JobTriggerView.as_view(), name='job_trigger'),
    path('<int:pk>/pause/', views.JobPauseView.as_view(), name='job_pause'),
    path('<int:pk>/resume/', views.JobResumeView.as_view(), name='job_resume'),

    # Job logs
    path('<int:pk>/logs/', views.JobLogListView.as_view(), name='job_logs'),
    path('<int:pk>/logs/<int:log_id>/', views.JobLogDetailView.as_view(), name='job_log_detail'),
    path('<int:pk>/logs/<int:log_id>/cancel/', views.JobCancelView.as_view(), name='job_cancel'),

    # Job health
    path('<int:pk>/health/', views.JobHealthView.as_view(), name='job_health'),

    # Statistics & Monitoring
    path('statistics/', views.JobStatisticsView.as_view(), name='job_statistics'),
    path('metrics/', views.SystemMetricsView.as_view(), name='system_metrics'),
    path('running/', views.RunningJobsView.as_view(), name='running_jobs'),
    path('failed-report/', views.FailedJobsReportView.as_view(), name='failed_report'),

    # Alerts
    path('alerts/', views.JobAlertListView.as_view(), name='job_alerts'),
    path('alerts/<int:pk>/acknowledge/', views.JobAlertAcknowledgeView.as_view(), name='alert_acknowledge'),

    # Schedule management
    path('sync-schedules/', views.SyncSchedulesView.as_view(), name='sync_schedules'),
]
