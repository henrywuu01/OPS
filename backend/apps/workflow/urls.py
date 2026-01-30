from django.urls import path
from . import views

urlpatterns = [
    # Workflow definition endpoints
    path('workflows/', views.WorkflowDefinitionListCreateView.as_view(), name='workflow_definition_list_create'),
    path('workflows/<int:pk>/', views.WorkflowDefinitionDetailView.as_view(), name='workflow_definition_detail'),
    path('workflows/<int:pk>/publish/', views.WorkflowDefinitionPublishView.as_view(), name='workflow_definition_publish'),

    # Approval instance endpoints
    path('approvals/', views.ApprovalListView.as_view(), name='approval_list'),
    path('approvals/create/', views.ApprovalCreateView.as_view(), name='approval_create'),
    path('approvals/<int:pk>/', views.ApprovalDetailView.as_view(), name='approval_detail'),
    path('approvals/<int:pk>/approve/', views.ApprovalApproveView.as_view(), name='approval_approve'),
    path('approvals/<int:pk>/reject/', views.ApprovalRejectView.as_view(), name='approval_reject'),
    path('approvals/<int:pk>/transfer/', views.ApprovalTransferView.as_view(), name='approval_transfer'),
    path('approvals/<int:pk>/withdraw/', views.ApprovalWithdrawView.as_view(), name='approval_withdraw'),
    path('approvals/<int:pk>/urge/', views.ApprovalUrgeView.as_view(), name='approval_urge'),
    path('approvals/<int:pk>/add-approver/', views.ApprovalAddApproverView.as_view(), name='approval_add_approver'),
    path('approvals/<int:pk>/comment/', views.ApprovalCommentView.as_view(), name='approval_comment'),

    # Task endpoints
    path('tasks/pending/', views.MyPendingTasksView.as_view(), name='my_pending_tasks'),
    path('tasks/completed/', views.MyCompletedTasksView.as_view(), name='my_completed_tasks'),
    path('tasks/cc/', views.MyCcApprovalsView.as_view(), name='my_cc_approvals'),
]
