from django.urls import path
from . import views

urlpatterns = [
    path('', views.MyNotificationListView.as_view(), name='notification_list'),
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='notification_detail'),
    path('<int:pk>/read/', views.NotificationMarkReadView.as_view(), name='notification_read'),
    path('read-all/', views.NotificationMarkAllReadView.as_view(), name='notification_read_all'),
    path('unread-count/', views.NotificationUnreadCountView.as_view(), name='notification_unread_count'),
]
