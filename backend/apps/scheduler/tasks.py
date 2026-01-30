"""
Celery tasks for job scheduling.
"""
import uuid
import subprocess
import requests
from datetime import datetime
from celery import shared_task
from django.utils import timezone
from django.conf import settings


@shared_task(bind=True, max_retries=3)
def execute_job(self, job_id, trigger_type='cron', trigger_user_id=None,
                input_params=None, flow_instance_id=None):
    """
    Execute a job.

    Args:
        job_id: Job ID to execute
        trigger_type: Type of trigger (cron, manual, flow, retry)
        trigger_user_id: User ID who triggered the job
        input_params: Optional input parameters
        flow_instance_id: Flow instance ID if triggered by a flow
    """
    from .models import Job, JobLog

    try:
        job = Job.objects.get(pk=job_id)
    except Job.DoesNotExist:
        return {'status': 'error', 'message': 'Job not found'}

    # Create log entry
    trace_id = str(uuid.uuid4())
    log = JobLog.objects.create(
        job=job,
        trace_id=trace_id,
        trigger_type=trigger_type,
        trigger_user_id=trigger_user_id,
        flow_instance_id=flow_instance_id,
        status='running',
        start_time=timezone.now(),
        input_params=input_params or {}
    )

    try:
        result = None
        error_msg = None

        if job.job_type == 'http':
            result = _execute_http_job(job, input_params)
        elif job.job_type == 'shell':
            result = _execute_shell_job(job, input_params)
        elif job.job_type == 'sql':
            result = _execute_sql_job(job, input_params)
        elif job.job_type == 'python':
            result = _execute_python_job(job, input_params)
        else:
            raise ValueError(f'Unknown job type: {job.job_type}')

        log.status = 'success'
        log.result = str(result)[:10000] if result else None

    except Exception as e:
        log.status = 'failed'
        error_msg = str(e)
        log.error_msg = error_msg

        # Retry if possible
        if self.request.retries < job.retry_count:
            log.save()
            self.retry(countdown=job.retry_interval, exc=e)

        # Send alert if configured
        if job.alert_on_failure:
            send_job_alert.delay(job_id, log.id, 'failure')

    finally:
        log.end_time = timezone.now()
        log.duration = int((log.end_time - log.start_time).total_seconds() * 1000)
        log.save()

    return {
        'status': log.status,
        'trace_id': trace_id,
        'duration': log.duration,
        'error_msg': error_msg
    }


def _execute_http_job(job, input_params=None):
    """Execute HTTP type job."""
    config = job.config
    url = config.get('url')
    method = config.get('method', 'GET').upper()
    headers = config.get('headers', {})
    body = config.get('body')

    # Merge input params
    if input_params:
        if isinstance(body, dict):
            body.update(input_params)
        else:
            body = input_params

    response = requests.request(
        method=method,
        url=url,
        headers=headers,
        json=body if method in ['POST', 'PUT', 'PATCH'] else None,
        params=body if method == 'GET' else None,
        timeout=job.timeout
    )

    response.raise_for_status()
    return response.text


def _execute_shell_job(job, input_params=None):
    """Execute shell script job."""
    config = job.config
    script = config.get('script')
    working_dir = config.get('working_dir', '/tmp')

    # Create environment with input params
    env = dict(config.get('env', {}))
    if input_params:
        for key, value in input_params.items():
            env[f'PARAM_{key.upper()}'] = str(value)

    result = subprocess.run(
        script,
        shell=True,
        cwd=working_dir,
        env=env,
        capture_output=True,
        text=True,
        timeout=job.timeout
    )

    if result.returncode != 0:
        raise RuntimeError(f'Script failed with code {result.returncode}: {result.stderr}')

    return result.stdout


def _execute_sql_job(job, input_params=None):
    """Execute SQL script job."""
    from django.db import connection

    config = job.config
    sql = config.get('sql')

    # Replace parameters in SQL
    if input_params:
        for key, value in input_params.items():
            sql = sql.replace(f':{key}', str(value))

    with connection.cursor() as cursor:
        cursor.execute(sql)
        if sql.strip().upper().startswith('SELECT'):
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        else:
            return f'Affected rows: {cursor.rowcount}'


def _execute_python_job(job, input_params=None):
    """Execute Python script job."""
    config = job.config
    script = config.get('script')

    # Create execution context
    local_vars = {
        'params': input_params or {},
        'result': None
    }

    exec(script, {'__builtins__': __builtins__}, local_vars)

    return local_vars.get('result')


@shared_task
def execute_job_flow(flow_id, trigger_user_id=None, input_params=None):
    """
    Execute a job flow (DAG workflow).

    Args:
        flow_id: Flow ID to execute
        trigger_user_id: User ID who triggered the flow
        input_params: Optional input parameters
    """
    from .models import JobFlow, JobFlowNode

    try:
        flow = JobFlow.objects.get(pk=flow_id)
    except JobFlow.DoesNotExist:
        return {'status': 'error', 'message': 'Flow not found'}

    flow_instance_id = str(uuid.uuid4())
    dag_config = flow.dag_config
    nodes = dag_config.get('nodes', [])
    edges = dag_config.get('edges', [])

    # Build dependency graph
    node_deps = {node['id']: [] for node in nodes}
    for edge in edges:
        source = edge.get('source')
        target = edge.get('target')
        if target in node_deps:
            node_deps[target].append(source)

    # Topological sort to determine execution order
    executed = set()
    results = {}

    def can_execute(node_id):
        return all(dep in executed for dep in node_deps.get(node_id, []))

    def get_ready_nodes():
        return [
            node['id'] for node in nodes
            if node['id'] not in executed and can_execute(node['id'])
        ]

    while len(executed) < len(nodes):
        ready = get_ready_nodes()
        if not ready:
            break

        for node_id in ready:
            node = next((n for n in nodes if n['id'] == node_id), None)
            if not node:
                continue

            job_id = node.get('job_id')
            if job_id:
                result = execute_job.apply(
                    args=[job_id],
                    kwargs={
                        'trigger_type': 'flow',
                        'trigger_user_id': trigger_user_id,
                        'input_params': input_params,
                        'flow_instance_id': flow_instance_id
                    }
                ).get()
                results[node_id] = result

            executed.add(node_id)

    return {
        'flow_instance_id': flow_instance_id,
        'results': results
    }


@shared_task
def send_job_alert(job_id, log_id, alert_type):
    """
    Send job alert notification.

    Args:
        job_id: Job ID
        log_id: Log ID
        alert_type: Type of alert (failure, timeout)
    """
    from .models import Job, JobLog
    from apps.notification.models import Notification

    try:
        job = Job.objects.get(pk=job_id)
        log = JobLog.objects.get(pk=log_id)
    except (Job.DoesNotExist, JobLog.DoesNotExist):
        return

    # Create notification
    if alert_type == 'failure':
        title = f'任务执行失败: {job.name}'
        content = f'任务 {job.name} 执行失败\n追踪ID: {log.trace_id}\n错误信息: {log.error_msg}'
    elif alert_type == 'timeout':
        title = f'任务执行超时: {job.name}'
        content = f'任务 {job.name} 执行超时\n追踪ID: {log.trace_id}'
    else:
        return

    # TODO: Send notifications via configured channels
    # For now, just log it
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f'Job Alert [{alert_type}]: {title}')
