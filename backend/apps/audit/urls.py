from django.urls import path
from . import views

urlpatterns = [
    # Audit log endpoints
    path('logs/', views.AuditLogListView.as_view(), name='audit_log_list'),
    path('logs/<int:pk>/', views.AuditLogDetailView.as_view(), name='audit_log_detail'),
    path('logs/export/', views.AuditLogExportView.as_view(), name='audit_log_export'),

    # Data change log endpoints
    path('data-changes/', views.DataChangeLogListView.as_view(), name='data_change_log_list'),
    path('data-changes/<int:pk>/', views.DataChangeLogDetailView.as_view(), name='data_change_log_detail'),

    # Login log endpoints
    path('login-logs/', views.LoginLogListView.as_view(), name='login_log_list'),

    # Alert rule endpoints
    path('alert-rules/', views.AlertRuleListCreateView.as_view(), name='alert_rule_list_create'),
    path('alert-rules/<int:pk>/', views.AlertRuleDetailView.as_view(), name='alert_rule_detail'),
    path('alert-rules/<int:pk>/status/', views.AlertRuleStatusView.as_view(), name='alert_rule_status'),

    # Alert history endpoints
    path('alerts/', views.AlertHistoryListView.as_view(), name='alert_history_list'),
    path('alerts/<int:pk>/', views.AlertHistoryDetailView.as_view(), name='alert_history_detail'),
    path('alerts/<int:pk>/acknowledge/', views.AlertHistoryAcknowledgeView.as_view(), name='alert_acknowledge'),
    path('alerts/<int:pk>/resolve/', views.AlertHistoryResolveView.as_view(), name='alert_resolve'),

    # Dashboard/Statistics endpoints
    path('dashboard/', views.SystemHealthDashboardView.as_view(), name='system_health_dashboard'),
    path('statistics/api/', views.ApiStatisticsView.as_view(), name='api_statistics'),
    path('online-users/', views.OnlineUsersView.as_view(), name='online_users'),
]
