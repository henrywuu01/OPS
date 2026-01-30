from django.urls import path
from . import views

urlpatterns = [
    # MetaTable endpoints
    path('tables/', views.MetaTableListCreateView.as_view(), name='meta_table_list_create'),
    path('tables/<int:pk>/', views.MetaTableDetailView.as_view(), name='meta_table_detail'),

    # Dynamic config table data endpoints
    path('<str:table_name>/', views.ConfigTableDataListCreateView.as_view(), name='config_table_data_list_create'),
    path('<str:table_name>/<int:pk>/', views.ConfigTableDataDetailView.as_view(), name='config_table_data_detail'),
    path('<str:table_name>/<int:pk>/history/', views.ConfigTableDataHistoryView.as_view(), name='config_table_data_history'),
    path('<str:table_name>/<int:pk>/rollback/', views.ConfigTableDataRollbackView.as_view(), name='config_table_data_rollback'),
    path('<str:table_name>/<int:pk>/diff/', views.ConfigTableDataDiffView.as_view(), name='config_table_data_diff'),

    # System config endpoints
    path('system/configs/', views.SystemConfigListView.as_view(), name='system_config_list'),
    path('system/configs/<str:key>/', views.SystemConfigDetailView.as_view(), name='system_config_detail'),

    # Config approval endpoints
    path('approvals/', views.ConfigApprovalListView.as_view(), name='config_approval_list'),
    path('approvals/<int:pk>/', views.ConfigApprovalDetailView.as_view(), name='config_approval_detail'),
    path('approvals/<int:pk>/approve/', views.ConfigApprovalApproveView.as_view(), name='config_approval_approve'),
    path('approvals/<int:pk>/reject/', views.ConfigApprovalRejectView.as_view(), name='config_approval_reject'),
]
