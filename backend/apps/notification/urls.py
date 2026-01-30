from django.urls import path
from . import views

urlpatterns = [
    # Message template endpoints
    path('templates/', views.MessageTemplateListCreateView.as_view(), name='message_template_list_create'),
    path('templates/<int:pk>/', views.MessageTemplateDetailView.as_view(), name='message_template_detail'),
    path('templates/<int:pk>/preview/', views.MessageTemplatePreviewView.as_view(), name='message_template_preview'),

    # Message log endpoints
    path('logs/', views.MessageLogListView.as_view(), name='message_log_list'),
    path('logs/<int:pk>/', views.MessageLogDetailView.as_view(), name='message_log_detail'),
    path('logs/<int:pk>/retry/', views.MessageLogRetryView.as_view(), name='message_log_retry'),

    # Send message endpoint
    path('send/', views.SendMessageView.as_view(), name='send_message'),

    # Internal notification endpoints
    path('notifications/', views.MyNotificationListView.as_view(), name='my_notification_list'),
    path('notifications/<int:pk>/', views.NotificationDetailView.as_view(), name='notification_detail'),
    path('notifications/<int:pk>/read/', views.NotificationMarkReadView.as_view(), name='notification_mark_read'),
    path('notifications/read-all/', views.NotificationMarkAllReadView.as_view(), name='notification_mark_all_read'),
    path('notifications/unread-count/', views.NotificationUnreadCountView.as_view(), name='notification_unread_count'),

    # Channel config endpoints
    path('channels/', views.ChannelConfigListView.as_view(), name='channel_config_list'),
    path('channels/<str:channel>/', views.ChannelConfigDetailView.as_view(), name='channel_config_detail'),
    path('channels/<str:channel>/test/', views.ChannelConfigTestView.as_view(), name='channel_config_test'),

    # User notification setting endpoints
    path('settings/', views.MyNotificationSettingsView.as_view(), name='my_notification_settings'),

    # Blacklist endpoints
    path('blacklist/', views.BlacklistListCreateView.as_view(), name='blacklist_list_create'),
    path('blacklist/<int:pk>/', views.BlacklistDeleteView.as_view(), name='blacklist_delete'),
]
