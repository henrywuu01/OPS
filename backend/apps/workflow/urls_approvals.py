from django.urls import path
from . import views

urlpatterns = [
    path('', views.ApprovalListView.as_view(), name='approval_list'),
    path('<int:pk>/', views.ApprovalDetailView.as_view(), name='approval_detail'),
    path('<int:pk>/approve/', views.ApprovalApproveView.as_view(), name='approval_approve'),
    path('<int:pk>/reject/', views.ApprovalRejectView.as_view(), name='approval_reject'),
    path('<int:pk>/transfer/', views.ApprovalTransferView.as_view(), name='approval_transfer'),
    path('<int:pk>/withdraw/', views.ApprovalWithdrawView.as_view(), name='approval_withdraw'),
    path('<int:pk>/urge/', views.ApprovalUrgeView.as_view(), name='approval_urge'),
]
