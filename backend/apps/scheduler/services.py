"""
Scheduler services for job scheduling, DAG execution, and monitoring.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Service for managing scheduled tasks with Celery Beat.
    Syncs Job/JobFlow cron expressions to PeriodicTask.
    """

    TASK_PREFIX_JOB = 'scheduler_job_'
    TASK_PREFIX_FLOW = 'scheduler_flow_'

    @classmethod
    def sync_job_schedule(cls, job) -> Optional[PeriodicTask]:
        """
        Sync a job's cron expression to Celery Beat PeriodicTask.

        Args:
            job: Job instance

        Returns:
            PeriodicTask instance or None
        """
        task_name = f'{cls.TASK_PREFIX_JOB}{job.id}'

        # Delete existing task if disabled or no cron
        if job.status != 'enabled' or not job.cron_expr:
            cls._delete_periodic_task(task_name)
            return None

        # Parse cron expression
        crontab = cls._parse_cron_expr(job.cron_expr)
        if not crontab:
            logger.warning(f'Invalid cron expression for job {job.id}: {job.cron_expr}')
            return None

        # Create or update PeriodicTask
        periodic_task, created = PeriodicTask.objects.update_or_create(
            name=task_name,
            defaults={
                'task': 'apps.scheduler.tasks.execute_job',
                'crontab': crontab,
                'args': json.dumps([job.id]),
                'kwargs': json.dumps({'trigger_type': 'cron'}),
                'enabled': True,
                'description': f'Scheduled job: {job.name}',
            }
        )

        logger.info(f"{'Created' if created else 'Updated'} periodic task for job {job.id}")
        return periodic_task

    @classmethod
    def sync_flow_schedule(cls, flow) -> Optional[PeriodicTask]:
        """
        Sync a flow's cron expression to Celery Beat PeriodicTask.

        Args:
            flow: JobFlow instance

        Returns:
            PeriodicTask instance or None
        """
        task_name = f'{cls.TASK_PREFIX_FLOW}{flow.id}'

        # Delete existing task if disabled or no cron
        if flow.status != 'enabled' or not flow.cron_expr:
            cls._delete_periodic_task(task_name)
            return None

        # Parse cron expression
        crontab = cls._parse_cron_expr(flow.cron_expr)
        if not crontab:
            logger.warning(f'Invalid cron expression for flow {flow.id}: {flow.cron_expr}')
            return None

        # Create or update PeriodicTask
        periodic_task, created = PeriodicTask.objects.update_or_create(
            name=task_name,
            defaults={
                'task': 'apps.scheduler.tasks.execute_job_flow',
                'crontab': crontab,
                'args': json.dumps([flow.id]),
                'kwargs': json.dumps({}),
                'enabled': True,
                'description': f'Scheduled flow: {flow.name}',
            }
        )

        logger.info(f"{'Created' if created else 'Updated'} periodic task for flow {flow.id}")
        return periodic_task

    @classmethod
    def sync_all_schedules(cls):
        """Sync all jobs and flows to Celery Beat."""
        from .models import Job, JobFlow

        synced_jobs = 0
        synced_flows = 0

        for job in Job.objects.filter(status='enabled', cron_expr__isnull=False):
            if cls.sync_job_schedule(job):
                synced_jobs += 1

        for flow in JobFlow.objects.filter(status='enabled', cron_expr__isnull=False):
            if cls.sync_flow_schedule(flow):
                synced_flows += 1

        logger.info(f'Synced {synced_jobs} jobs and {synced_flows} flows to Celery Beat')
        return {'jobs': synced_jobs, 'flows': synced_flows}

    @classmethod
    def remove_job_schedule(cls, job_id: int):
        """Remove a job's periodic task."""
        task_name = f'{cls.TASK_PREFIX_JOB}{job_id}'
        cls._delete_periodic_task(task_name)

    @classmethod
    def remove_flow_schedule(cls, flow_id: int):
        """Remove a flow's periodic task."""
        task_name = f'{cls.TASK_PREFIX_FLOW}{flow_id}'
        cls._delete_periodic_task(task_name)

    @classmethod
    def _parse_cron_expr(cls, cron_expr: str) -> Optional[CrontabSchedule]:
        """
        Parse cron expression and create CrontabSchedule.

        Supports standard 5-part cron: minute hour day_of_month month day_of_week
        """
        parts = cron_expr.strip().split()
        if len(parts) < 5:
            return None

        try:
            crontab, _ = CrontabSchedule.objects.get_or_create(
                minute=parts[0],
                hour=parts[1],
                day_of_month=parts[2],
                month_of_year=parts[3],
                day_of_week=parts[4],
            )
            return crontab
        except Exception as e:
            logger.error(f'Failed to parse cron expression: {e}')
            return None

    @classmethod
    def _delete_periodic_task(cls, task_name: str):
        """Delete a periodic task by name."""
        deleted, _ = PeriodicTask.objects.filter(name=task_name).delete()
        if deleted:
            logger.info(f'Deleted periodic task: {task_name}')


class DAGExecutionEngine:
    """
    Advanced DAG workflow execution engine with parallel execution,
    conditional branching, and error handling.
    """

    ERROR_STRATEGY_FAIL_FAST = 'fail_fast'
    ERROR_STRATEGY_CONTINUE = 'continue'
    ERROR_STRATEGY_SKIP_DOWNSTREAM = 'skip_downstream'

    def __init__(self, flow, trigger_user_id=None, input_params=None):
        """
        Initialize DAG execution engine.

        Args:
            flow: JobFlow instance
            trigger_user_id: User ID who triggered the flow
            input_params: Initial input parameters
        """
        self.flow = flow
        self.trigger_user_id = trigger_user_id
        self.input_params = input_params or {}
        self.flow_instance_id = None
        self.dag_config = flow.dag_config
        self.nodes = {n['id']: n for n in self.dag_config.get('nodes', [])}
        self.edges = self.dag_config.get('edges', [])
        self.error_strategy = self.dag_config.get('error_strategy', self.ERROR_STRATEGY_FAIL_FAST)
        self.max_parallel = self.dag_config.get('max_parallel', 5)

        # Execution state
        self.results = {}
        self.status = {}  # node_id -> status
        self.failed_nodes = set()
        self.skipped_nodes = set()

    def execute(self) -> Dict[str, Any]:
        """
        Execute the DAG workflow.

        Returns:
            Execution result dictionary
        """
        import uuid
        from .models import JobLog, FlowInstance

        self.flow_instance_id = str(uuid.uuid4())

        # Create flow instance record
        flow_instance = FlowInstance.objects.create(
            flow=self.flow,
            instance_id=self.flow_instance_id,
            trigger_user_id=self.trigger_user_id,
            input_params=self.input_params,
            status='running',
            start_time=timezone.now(),
        )

        try:
            # Build dependency graph
            dependencies = self._build_dependencies()
            dependents = self._build_dependents()

            # Execute nodes in topological order with parallelism
            executed = set()
            pending = set(self.nodes.keys())

            while pending:
                # Find nodes ready to execute
                ready_nodes = [
                    node_id for node_id in pending
                    if self._can_execute(node_id, dependencies, executed)
                ]

                if not ready_nodes:
                    # No more nodes can execute
                    if pending:
                        logger.warning(f'Flow {self.flow.id} has unreachable nodes: {pending}')
                        for node_id in pending:
                            self.skipped_nodes.add(node_id)
                            self.status[node_id] = 'skipped'
                    break

                # Execute ready nodes in parallel
                with ThreadPoolExecutor(max_workers=min(len(ready_nodes), self.max_parallel)) as executor:
                    futures = {
                        executor.submit(self._execute_node, node_id): node_id
                        for node_id in ready_nodes
                    }

                    for future in as_completed(futures):
                        node_id = futures[future]
                        try:
                            result = future.result()
                            self.results[node_id] = result
                            self.status[node_id] = result.get('status', 'unknown')

                            if result.get('status') == 'failed':
                                self.failed_nodes.add(node_id)

                                if self.error_strategy == self.ERROR_STRATEGY_FAIL_FAST:
                                    # Mark all pending as skipped
                                    for p in pending:
                                        if p != node_id:
                                            self.skipped_nodes.add(p)
                                            self.status[p] = 'skipped'
                                    pending.clear()
                                    break
                                elif self.error_strategy == self.ERROR_STRATEGY_SKIP_DOWNSTREAM:
                                    # Mark downstream nodes as skipped
                                    downstream = self._get_downstream_nodes(node_id, dependents)
                                    for d in downstream:
                                        self.skipped_nodes.add(d)
                                        self.status[d] = 'skipped'
                                        pending.discard(d)

                        except Exception as e:
                            logger.error(f'Error executing node {node_id}: {e}')
                            self.results[node_id] = {'status': 'failed', 'error': str(e)}
                            self.status[node_id] = 'failed'
                            self.failed_nodes.add(node_id)

                        executed.add(node_id)
                        pending.discard(node_id)

            # Determine overall status
            if self.failed_nodes:
                overall_status = 'failed'
            elif self.skipped_nodes:
                overall_status = 'partial'
            else:
                overall_status = 'success'

            # Update flow instance
            flow_instance.status = overall_status
            flow_instance.end_time = timezone.now()
            flow_instance.duration = int((flow_instance.end_time - flow_instance.start_time).total_seconds() * 1000)
            flow_instance.result = {
                'node_results': self.results,
                'node_status': self.status,
                'failed_nodes': list(self.failed_nodes),
                'skipped_nodes': list(self.skipped_nodes),
            }
            flow_instance.save()

            return {
                'flow_instance_id': self.flow_instance_id,
                'status': overall_status,
                'results': self.results,
                'failed_nodes': list(self.failed_nodes),
                'skipped_nodes': list(self.skipped_nodes),
            }

        except Exception as e:
            logger.error(f'Flow execution error: {e}')
            flow_instance.status = 'failed'
            flow_instance.end_time = timezone.now()
            flow_instance.error_msg = str(e)
            flow_instance.save()

            return {
                'flow_instance_id': self.flow_instance_id,
                'status': 'failed',
                'error': str(e),
            }

    def _build_dependencies(self) -> Dict[str, List[str]]:
        """Build node dependencies (what each node depends on)."""
        deps = defaultdict(list)
        for edge in self.edges:
            target = edge.get('target')
            source = edge.get('source')
            if target and source:
                deps[target].append(source)
        return deps

    def _build_dependents(self) -> Dict[str, List[str]]:
        """Build node dependents (what depends on each node)."""
        deps = defaultdict(list)
        for edge in self.edges:
            source = edge.get('source')
            target = edge.get('target')
            if source and target:
                deps[source].append(target)
        return deps

    def _can_execute(self, node_id: str, dependencies: Dict, executed: set) -> bool:
        """Check if a node can be executed."""
        if node_id in self.skipped_nodes:
            return False

        node = self.nodes.get(node_id)
        if not node:
            return False

        # Check all dependencies are executed
        deps = dependencies.get(node_id, [])
        for dep in deps:
            if dep not in executed:
                return False
            # Skip if dependency failed and using skip_downstream strategy
            if dep in self.failed_nodes and self.error_strategy == self.ERROR_STRATEGY_SKIP_DOWNSTREAM:
                return False

        # Check condition if exists
        condition = node.get('condition')
        if condition:
            return self._evaluate_condition(condition)

        return True

    def _execute_node(self, node_id: str) -> Dict[str, Any]:
        """Execute a single node."""
        from .tasks import execute_job

        node = self.nodes.get(node_id)
        if not node:
            return {'status': 'failed', 'error': 'Node not found'}

        job_id = node.get('job_id')
        if not job_id:
            # Virtual node (start/end/condition)
            return {'status': 'success', 'result': 'virtual_node'}

        # Merge node-level params with flow params
        node_params = node.get('params', {})
        merged_params = {**self.input_params, **node_params}

        # Add upstream results to params
        upstream_results = node.get('upstream_results')
        if upstream_results:
            for upstream_node_id, param_name in upstream_results.items():
                if upstream_node_id in self.results:
                    merged_params[param_name] = self.results[upstream_node_id].get('result')

        # Execute job synchronously
        result = execute_job.apply(
            args=[job_id],
            kwargs={
                'trigger_type': 'flow',
                'trigger_user_id': self.trigger_user_id,
                'input_params': merged_params,
                'flow_instance_id': self.flow_instance_id,
            }
        ).get()

        return result

    def _evaluate_condition(self, condition: Dict) -> bool:
        """Evaluate a condition expression."""
        condition_type = condition.get('type')
        value = condition.get('value')

        if condition_type == 'always':
            return True
        elif condition_type == 'node_success':
            node_id = condition.get('node_id')
            return self.status.get(node_id) == 'success'
        elif condition_type == 'node_failed':
            node_id = condition.get('node_id')
            return self.status.get(node_id) == 'failed'
        elif condition_type == 'expression':
            # Evaluate Python expression with results context
            try:
                return eval(value, {'results': self.results, 'status': self.status})
            except Exception:
                return False

        return True

    def _get_downstream_nodes(self, node_id: str, dependents: Dict) -> set:
        """Get all downstream nodes recursively."""
        downstream = set()
        to_visit = list(dependents.get(node_id, []))

        while to_visit:
            current = to_visit.pop()
            if current not in downstream:
                downstream.add(current)
                to_visit.extend(dependents.get(current, []))

        return downstream


class JobMonitoringService:
    """
    Service for job monitoring, metrics collection, and alerting.
    """

    @classmethod
    def get_job_health(cls, job_id: int, hours: int = 24) -> Dict[str, Any]:
        """
        Get job health metrics.

        Args:
            job_id: Job ID
            hours: Number of hours to look back

        Returns:
            Health metrics dictionary
        """
        from .models import Job, JobLog

        try:
            job = Job.objects.get(pk=job_id)
        except Job.DoesNotExist:
            return {'error': 'Job not found'}

        since = timezone.now() - timedelta(hours=hours)
        logs = JobLog.objects.filter(job=job, start_time__gte=since)

        total = logs.count()
        success = logs.filter(status='success').count()
        failed = logs.filter(status='failed').count()
        timeout = logs.filter(status='timeout').count()

        # Calculate average duration
        success_logs = logs.filter(status='success', duration__isnull=False)
        avg_duration = 0
        if success_logs.exists():
            durations = list(success_logs.values_list('duration', flat=True))
            avg_duration = sum(durations) / len(durations)

        # Get last execution
        last_log = logs.first()

        return {
            'job_id': job_id,
            'job_name': job.name,
            'status': job.status,
            'period_hours': hours,
            'total_executions': total,
            'success_count': success,
            'failed_count': failed,
            'timeout_count': timeout,
            'success_rate': round(success / total * 100, 2) if total else 0,
            'avg_duration_ms': round(avg_duration, 2),
            'last_execution': {
                'status': last_log.status if last_log else None,
                'time': last_log.start_time.isoformat() if last_log else None,
                'duration_ms': last_log.duration if last_log else None,
            } if last_log else None,
        }

    @classmethod
    def get_system_metrics(cls) -> Dict[str, Any]:
        """Get overall scheduler system metrics."""
        from .models import Job, JobFlow, JobLog, FlowInstance

        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        return {
            'jobs': {
                'total': Job.objects.count(),
                'enabled': Job.objects.filter(status='enabled').count(),
                'with_schedule': Job.objects.filter(cron_expr__isnull=False).exclude(cron_expr='').count(),
            },
            'flows': {
                'total': JobFlow.objects.count(),
                'enabled': JobFlow.objects.filter(status='enabled').count(),
            },
            'executions_today': {
                'total': JobLog.objects.filter(start_time__gte=today_start).count(),
                'success': JobLog.objects.filter(start_time__gte=today_start, status='success').count(),
                'failed': JobLog.objects.filter(start_time__gte=today_start, status='failed').count(),
            },
            'executions_week': {
                'total': JobLog.objects.filter(start_time__gte=week_start).count(),
                'success': JobLog.objects.filter(start_time__gte=week_start, status='success').count(),
                'failed': JobLog.objects.filter(start_time__gte=week_start, status='failed').count(),
            },
            'flow_instances_today': FlowInstance.objects.filter(start_time__gte=today_start).count(),
            'running_jobs': JobLog.objects.filter(status='running').count(),
        }

    @classmethod
    def get_failed_jobs_report(cls, hours: int = 24) -> List[Dict]:
        """Get report of failed jobs in the specified period."""
        from .models import JobLog

        since = timezone.now() - timedelta(hours=hours)
        failed_logs = JobLog.objects.filter(
            start_time__gte=since,
            status='failed'
        ).select_related('job', 'trigger_user').order_by('-start_time')

        report = []
        for log in failed_logs:
            report.append({
                'job_id': log.job_id,
                'job_name': log.job.name,
                'trace_id': log.trace_id,
                'trigger_type': log.trigger_type,
                'trigger_user': log.trigger_user.username if log.trigger_user else None,
                'start_time': log.start_time.isoformat(),
                'error_msg': log.error_msg[:500] if log.error_msg else None,
            })

        return report


class AlertService:
    """
    Service for sending job alerts via multiple channels.
    """

    CHANNEL_EMAIL = 'email'
    CHANNEL_SMS = 'sms'
    CHANNEL_WECHAT = 'wechat'
    CHANNEL_DINGTALK = 'dingtalk'
    CHANNEL_FEISHU = 'feishu'
    CHANNEL_WEBHOOK = 'webhook'

    @classmethod
    def send_alert(cls, job, log, alert_type: str):
        """
        Send alert for a job execution.

        Args:
            job: Job instance
            log: JobLog instance
            alert_type: Type of alert (failure, timeout, success)
        """
        from apps.notification.services import NotificationService

        channels = job.alert_channels or ['email']

        # Build alert content
        context = {
            'job_id': job.id,
            'job_name': job.name,
            'job_type': job.job_type,
            'trace_id': log.trace_id,
            'status': log.status,
            'trigger_type': log.trigger_type,
            'start_time': log.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': log.end_time.strftime('%Y-%m-%d %H:%M:%S') if log.end_time else '-',
            'duration_ms': log.duration,
            'error_msg': log.error_msg or '',
        }

        if alert_type == 'failure':
            title = f'[告警] 任务执行失败: {job.name}'
            content = cls._render_failure_alert(context)
        elif alert_type == 'timeout':
            title = f'[告警] 任务执行超时: {job.name}'
            content = cls._render_timeout_alert(context)
        elif alert_type == 'success':
            title = f'[通知] 任务执行成功: {job.name}'
            content = cls._render_success_alert(context)
        else:
            return

        # Send via each channel
        for channel in channels:
            try:
                if channel == cls.CHANNEL_EMAIL:
                    cls._send_email_alert(job, title, content)
                elif channel == cls.CHANNEL_DINGTALK:
                    cls._send_dingtalk_alert(job, title, content)
                elif channel == cls.CHANNEL_FEISHU:
                    cls._send_feishu_alert(job, title, content)
                elif channel == cls.CHANNEL_WEBHOOK:
                    cls._send_webhook_alert(job, context)
                else:
                    logger.warning(f'Unknown alert channel: {channel}')
            except Exception as e:
                logger.error(f'Failed to send alert via {channel}: {e}')

        # Create notification record
        try:
            from apps.notification.models import Notification
            Notification.objects.create(
                title=title,
                content=content[:500],
                type='alert',
                priority='high' if alert_type == 'failure' else 'normal',
            )
        except Exception as e:
            logger.error(f'Failed to create notification: {e}')

    @classmethod
    def _render_failure_alert(cls, context: Dict) -> str:
        """Render failure alert content."""
        return f"""
任务执行失败告警

任务名称: {context['job_name']}
任务类型: {context['job_type']}
追踪ID: {context['trace_id']}
触发类型: {context['trigger_type']}
开始时间: {context['start_time']}
结束时间: {context['end_time']}
执行耗时: {context['duration_ms']}ms

错误信息:
{context['error_msg']}

请及时处理!
        """.strip()

    @classmethod
    def _render_timeout_alert(cls, context: Dict) -> str:
        """Render timeout alert content."""
        return f"""
任务执行超时告警

任务名称: {context['job_name']}
任务类型: {context['job_type']}
追踪ID: {context['trace_id']}
触发类型: {context['trigger_type']}
开始时间: {context['start_time']}
执行耗时: {context['duration_ms']}ms

请检查任务配置或系统资源!
        """.strip()

    @classmethod
    def _render_success_alert(cls, context: Dict) -> str:
        """Render success notification content."""
        return f"""
任务执行成功通知

任务名称: {context['job_name']}
追踪ID: {context['trace_id']}
开始时间: {context['start_time']}
结束时间: {context['end_time']}
执行耗时: {context['duration_ms']}ms
        """.strip()

    @classmethod
    def _send_email_alert(cls, job, title: str, content: str):
        """Send alert via email."""
        # Get alert recipients from job config or default
        recipients = job.config.get('alert_emails', [])
        if not recipients:
            logger.warning(f'No email recipients configured for job {job.id}')
            return

        try:
            from django.core.mail import send_mail
            send_mail(
                subject=title,
                message=content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False,
            )
            logger.info(f'Sent email alert for job {job.id}')
        except Exception as e:
            logger.error(f'Failed to send email alert: {e}')

    @classmethod
    def _send_dingtalk_alert(cls, job, title: str, content: str):
        """Send alert via DingTalk webhook."""
        import requests

        webhook_url = job.config.get('dingtalk_webhook')
        if not webhook_url:
            logger.warning(f'No DingTalk webhook configured for job {job.id}')
            return

        try:
            response = requests.post(webhook_url, json={
                'msgtype': 'text',
                'text': {'content': f'{title}\n\n{content}'}
            }, timeout=10)
            response.raise_for_status()
            logger.info(f'Sent DingTalk alert for job {job.id}')
        except Exception as e:
            logger.error(f'Failed to send DingTalk alert: {e}')

    @classmethod
    def _send_feishu_alert(cls, job, title: str, content: str):
        """Send alert via Feishu webhook."""
        import requests

        webhook_url = job.config.get('feishu_webhook')
        if not webhook_url:
            logger.warning(f'No Feishu webhook configured for job {job.id}')
            return

        try:
            response = requests.post(webhook_url, json={
                'msg_type': 'text',
                'content': {'text': f'{title}\n\n{content}'}
            }, timeout=10)
            response.raise_for_status()
            logger.info(f'Sent Feishu alert for job {job.id}')
        except Exception as e:
            logger.error(f'Failed to send Feishu alert: {e}')

    @classmethod
    def _send_webhook_alert(cls, job, context: Dict):
        """Send alert via custom webhook."""
        import requests

        webhook_url = job.config.get('alert_webhook')
        if not webhook_url:
            logger.warning(f'No alert webhook configured for job {job.id}')
            return

        try:
            response = requests.post(webhook_url, json=context, timeout=10)
            response.raise_for_status()
            logger.info(f'Sent webhook alert for job {job.id}')
        except Exception as e:
            logger.error(f'Failed to send webhook alert: {e}')
