from django.urls import path
from . import views

urlpatterns = [
    # DataSource endpoints
    path('datasources/', views.DataSourceListCreateView.as_view(), name='datasource_list_create'),
    path('datasources/<int:pk>/', views.DataSourceDetailView.as_view(), name='datasource_detail'),
    path('datasources/<int:pk>/test/', views.DataSourceTestView.as_view(), name='datasource_test'),

    # Report endpoints
    path('reports/', views.ReportListCreateView.as_view(), name='report_list_create'),
    path('reports/<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('reports/<int:pk>/query/', views.ReportQueryView.as_view(), name='report_query'),
    path('reports/<int:pk>/export/', views.ReportExportView.as_view(), name='report_export'),
    path('reports/<int:pk>/publish/', views.ReportPublishView.as_view(), name='report_publish'),

    # Subscription endpoints
    path('reports/<int:pk>/subscriptions/', views.ReportSubscriptionListCreateView.as_view(), name='report_subscription_list_create'),
    path('reports/<int:pk>/subscriptions/<int:sub_id>/', views.ReportSubscriptionDetailView.as_view(), name='report_subscription_detail'),

    # Favorite endpoints
    path('reports/<int:pk>/favorite/', views.ReportFavoriteView.as_view(), name='report_favorite'),
    path('favorites/', views.MyFavoriteReportsView.as_view(), name='my_favorite_reports'),
]
