"""
Workflow engine for approval processing.
"""
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.db import transaction
from apps.auth.models import User, Role
from .models import (
    WorkflowDefinition, ApprovalInstance, ApprovalRecord,
    ApprovalTask, ApprovalCc
)


class WorkflowEngine:
    """Workflow execution engine."""

    def __init__(self, instance: ApprovalInstance):
        self.instance = instance
        self.workflow = instance.workflow
        self.nodes = {node['id']: node for node in (self.workflow.nodes or [])}
        self.edges = self.workflow.edges or []

    def start(self) -> ApprovalInstance:
        """Start the workflow instance."""
        with transaction.atomic():
            # Find start node
            start_node = self._find_start_node()
            if not start_node:
                raise ValueError('未找到开始节点')

            # Move to first approval node
            next_nodes = self._get_next_nodes(start_node['id'])
            if next_nodes:
                self.instance.current_node = next_nodes[0]['id']
                self._create_tasks(next_nodes[0])

            self.instance.status = 'pending'
            self.instance.submitted_at = timezone.now()
            self.instance.save()

            # Create submit record
            ApprovalRecord.objects.create(
                instance=self.instance,
                node_id='start',
                node_name='提交申请',
                approver=self.instance.applicant,
                action='submit'
            )

            return self.instance

    def approve(self, task: ApprovalTask, user: User, comment: str = None,
                attachments: List = None) -> ApprovalInstance:
        """Approve the current task."""
        with transaction.atomic():
            node = self.nodes.get(task.node_id)
            if not node:
                raise ValueError('节点不存在')

            # Complete current task
            task.status = 'completed'
            task.completed_at = timezone.now()
            task.save()

            # Create approval record
            ApprovalRecord.objects.create(
                instance=self.instance,
                node_id=task.node_id,
                node_name=task.node_name,
                approver=user,
                action='approve',
                comment=comment,
                attachments=attachments or []
            )

            # Check if all tasks for this node are completed (for counter-sign)
            node_type = node.get('type', 'single')
            if node_type == 'countersign':
                pending_tasks = self.instance.tasks.filter(
                    node_id=task.node_id, status='pending'
                )
                if pending_tasks.exists():
                    return self.instance

            # Move to next node
            self._move_to_next(node)

            return self.instance

    def reject(self, task: ApprovalTask, user: User, comment: str = None,
               attachments: List = None) -> ApprovalInstance:
        """Reject the current task."""
        with transaction.atomic():
            # Complete current task
            task.status = 'completed'
            task.completed_at = timezone.now()
            task.save()

            # Cancel other pending tasks
            self.instance.tasks.filter(status='pending').update(
                status='cancelled'
            )

            # Create rejection record
            ApprovalRecord.objects.create(
                instance=self.instance,
                node_id=task.node_id,
                node_name=task.node_name,
                approver=user,
                action='reject',
                comment=comment,
                attachments=attachments or []
            )

            # Update instance status
            self.instance.status = 'rejected'
            self.instance.completed_at = timezone.now()
            self.instance.save()

            # Execute rejection callback
            self._execute_callback('reject')

            return self.instance

    def transfer(self, task: ApprovalTask, user: User, transfer_to: User,
                 comment: str = None) -> ApprovalInstance:
        """Transfer approval to another user."""
        with transaction.atomic():
            # Complete current task
            task.status = 'transferred'
            task.completed_at = timezone.now()
            task.save()

            # Create new task for transfer_to user
            ApprovalTask.objects.create(
                instance=self.instance,
                node_id=task.node_id,
                node_name=task.node_name,
                assign_type='user',
                assignee=transfer_to,
                status='pending'
            )

            # Create transfer record
            ApprovalRecord.objects.create(
                instance=self.instance,
                node_id=task.node_id,
                node_name=task.node_name,
                approver=user,
                action='transfer',
                comment=comment,
                transfer_to=transfer_to
            )

            return self.instance

    def withdraw(self, user: User) -> ApprovalInstance:
        """Withdraw the approval application."""
        with transaction.atomic():
            if self.instance.applicant != user:
                raise ValueError('只有申请人可以撤回')

            if self.instance.status != 'pending':
                raise ValueError('只能撤回审批中的申请')

            # Cancel all pending tasks
            self.instance.tasks.filter(status='pending').update(
                status='cancelled'
            )

            # Create withdraw record
            ApprovalRecord.objects.create(
                instance=self.instance,
                node_id=self.instance.current_node or 'withdraw',
                node_name='撤回',
                approver=user,
                action='withdraw'
            )

            self.instance.status = 'withdrawn'
            self.instance.completed_at = timezone.now()
            self.instance.save()

            return self.instance

    def add_comment(self, user: User, comment: str,
                    attachments: List = None) -> ApprovalRecord:
        """Add a comment to the approval."""
        return ApprovalRecord.objects.create(
            instance=self.instance,
            node_id=self.instance.current_node or 'comment',
            node_name='评论',
            approver=user,
            action='comment',
            comment=comment,
            attachments=attachments or []
        )

    def urge(self, user: User) -> bool:
        """Send urge notification to current approvers."""
        with transaction.atomic():
            pending_tasks = self.instance.tasks.filter(status='pending')
            if not pending_tasks.exists():
                return False

            # Update reminded count
            pending_tasks.update(
                reminded_count=transaction.F('reminded_count') + 1,
                last_reminded_at=timezone.now()
            )

            # Create urge record
            ApprovalRecord.objects.create(
                instance=self.instance,
                node_id=self.instance.current_node or 'urge',
                node_name='催办',
                approver=user,
                action='urge'
            )

            # TODO: Send notification to assignees
            return True

    def _find_start_node(self) -> Optional[Dict]:
        """Find the start node in workflow."""
        for node in self.nodes.values():
            if node.get('type') == 'start':
                return node
        return None

    def _find_end_node(self) -> Optional[Dict]:
        """Find the end node in workflow."""
        for node in self.nodes.values():
            if node.get('type') == 'end':
                return node
        return None

    def _get_next_nodes(self, node_id: str) -> List[Dict]:
        """Get next nodes after the given node."""
        next_node_ids = []
        for edge in self.edges:
            if edge.get('source') == node_id:
                # Check condition if exists
                condition = edge.get('condition')
                if condition:
                    if not self._evaluate_condition(condition):
                        continue
                next_node_ids.append(edge.get('target'))

        return [self.nodes[nid] for nid in next_node_ids if nid in self.nodes]

    def _evaluate_condition(self, condition: Dict) -> bool:
        """Evaluate edge condition."""
        field = condition.get('field')
        operator = condition.get('operator')
        value = condition.get('value')

        form_value = self.instance.form_data.get(field)

        if operator == 'eq':
            return form_value == value
        elif operator == 'ne':
            return form_value != value
        elif operator == 'gt':
            return float(form_value or 0) > float(value)
        elif operator == 'lt':
            return float(form_value or 0) < float(value)
        elif operator == 'gte':
            return float(form_value or 0) >= float(value)
        elif operator == 'lte':
            return float(form_value or 0) <= float(value)
        elif operator == 'in':
            return form_value in value
        elif operator == 'contains':
            return value in (form_value or '')

        return True

    def _move_to_next(self, current_node: Dict):
        """Move workflow to next node."""
        next_nodes = self._get_next_nodes(current_node['id'])

        if not next_nodes:
            # No next node, workflow ends
            self._complete_workflow()
            return

        next_node = next_nodes[0]

        if next_node.get('type') == 'end':
            self._complete_workflow()
            return

        # Create tasks for next node
        self.instance.current_node = next_node['id']
        self.instance.save()
        self._create_tasks(next_node)

        # Handle CC
        cc_users = next_node.get('cc_users', [])
        for user_id in cc_users:
            ApprovalCc.objects.get_or_create(
                instance=self.instance,
                user_id=user_id,
                defaults={'node_id': next_node['id']}
            )

    def _create_tasks(self, node: Dict):
        """Create approval tasks for a node."""
        assign_type = node.get('assign_type', 'user')
        assignees = []

        if assign_type == 'user':
            assignees = node.get('assignees', [])
        elif assign_type == 'role':
            role_ids = node.get('roles', [])
            assignees = list(
                User.objects.filter(
                    user_roles__role_id__in=role_ids,
                    is_active=True
                ).values_list('id', flat=True)
            )
        elif assign_type == 'department':
            # Get department leader
            dept = self.instance.applicant.department
            if dept and dept.leader_id:
                assignees = [dept.leader_id]
        elif assign_type == 'applicant_select':
            # Assignees should be in form_data
            assignees = self.instance.form_data.get(f'{node["id"]}_assignees', [])

        for user_id in assignees:
            ApprovalTask.objects.create(
                instance=self.instance,
                node_id=node['id'],
                node_name=node.get('name', ''),
                assign_type=assign_type,
                assignee_id=user_id,
                status='pending',
                due_time=self._calculate_due_time(node)
            )

    def _calculate_due_time(self, node: Dict):
        """Calculate task due time based on node config."""
        timeout_hours = node.get('timeout_hours')
        if timeout_hours:
            return timezone.now() + timezone.timedelta(hours=timeout_hours)
        return None

    def _complete_workflow(self):
        """Complete the workflow."""
        self.instance.status = 'approved'
        self.instance.completed_at = timezone.now()
        self.instance.current_node = None
        self.instance.save()

        # Execute approval callback
        self._execute_callback('approve')

    def _execute_callback(self, action: str):
        """Execute callback after workflow completion."""
        callback_config = self.workflow.callback_config or {}
        callback_url = callback_config.get(f'{action}_url')

        if callback_url:
            import requests
            try:
                requests.post(callback_url, json={
                    'instance_id': self.instance.id,
                    'business_type': self.instance.business_type,
                    'business_id': self.instance.business_id,
                    'action': action,
                    'form_data': self.instance.form_data
                }, timeout=10)
            except Exception:
                pass
