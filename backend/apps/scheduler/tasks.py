"""
Celery tasks for job scheduling.
"""
import uuid
import subprocess
import requests
import logging
from datetime import datetime
from celery import shared_task
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


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
    from .models import Job, JobLog, JobFlow

    try:
        job = Job.objects.get(pk=job_id)
    except Job.DoesNotExist:
        logger.error(f'Job {job_id} not found')
        return {'status': 'error', 'message': 'Job not found'}

    # Get flow if flow_instance_id is provided
    flow = None
    if flow_instance_id:
        from .models import FlowInstance
        try:
            flow_instance = FlowInstance.objects.get(instance_id=flow_instance_id)
            flow = flow_instance.flow
        except FlowInstance.DoesNotExist:
            pass

    # Create log entry
    trace_id = str(uuid.uuid4())
    log = JobLog.objects.create(
        job=job,
        flow=flow,
        trace_id=trace_id,
        trigger_type=trigger_type,
        trigger_user_id=trigger_user_id,
        flow_instance_id=flow_instance_id,
        status='running',
        start_time=timezone.now(),
        input_params=input_params or {},
        retry_count=self.request.retries,
    )

    logger.info(f'Starting job {job.id} ({job.name}), trace_id: {trace_id}')

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
        logger.info(f'Job {job.id} completed successfully, trace_id: {trace_id}')

    except subprocess.TimeoutExpired:
        log.status = 'timeout'
        error_msg = f'Job timed out after {job.timeout} seconds'
        log.error_msg = error_msg
        logger.warning(f'Job {job.id} timed out, trace_id: {trace_id}')

        # Send timeout alert
        if job.alert_on_timeout:
            send_job_alert.delay(job_id, log.id, 'timeout')

    except Exception as e:
        log.status = 'failed'
        error_msg = str(e)
        log.error_msg = error_msg
        logger.error(f'Job {job.id} failed: {error_msg}, trace_id: {trace_id}')

        # Retry if possible
        if self.request.retries < job.retry_count:
            log.save()
            logger.info(f'Retrying job {job.id}, attempt {self.request.retries + 1}/{job.retry_count}')
            raise self.retry(countdown=job.retry_interval, exc=e)

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
        'result': log.result[:500] if log.result else None,
        'error_msg': error_msg
    }


def _execute_http_job(job, input_params=None):
    """Execute HTTP type job."""
    config = job.config
    url = config.get('url')
    method = config.get('method', 'GET').upper()
    headers = config.get('headers', {})
    body = config.get('body')

    if not url:
        raise ValueError('HTTP job requires url in config')

    # Merge input params
    if input_params:
        if isinstance(body, dict):
            body = {**body, **input_params}
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
    import os

    config = job.config
    script = config.get('script')
    working_dir = config.get('working_dir', '/tmp')

    if not script:
        raise ValueError('Shell job requires script in config')

    # Create environment with input params
    env = os.environ.copy()
    env.update(config.get('env', {}))
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
    from django.db import connection, connections

    config = job.config
    sql = config.get('sql')
    database = config.get('database', 'default')

    if not sql:
        raise ValueError('SQL job requires sql in config')

    # Replace parameters in SQL
    if input_params:
        for key, value in input_params.items():
            sql = sql.replace(f':{key}', str(value))
            sql = sql.replace(f'${key}', str(value))

    conn = connections[database] if database != 'default' else connection

    with conn.cursor() as cursor:
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

    if not script:
        raise ValueError('Python job requires script in config')

    # Create execution context with limited builtins for security
    safe_builtins = {
        'print': print,
        'len': len,
        'range': range,
        'str': str,
        'int': int,
        'float': float,
        'bool': bool,
        'list': list,
        'dict': dict,
        'set': set,
        'tuple': tuple,
        'sum': sum,
        'min': min,
        'max': max,
        'abs': abs,
        'round': round,
        'sorted': sorted,
        'enumerate': enumerate,
        'zip': zip,
        'map': map,
        'filter': filter,
        'isinstance': isinstance,
        'type': type,
        'None': None,
        'True': True,
        'False': False,
    }

    local_vars = {
        'params': input_params or {},
        'result': None
    }

    exec(script, {'__builtins__': safe_builtins}, local_vars)

    return local_vars.get('result')


@shared_task
def execute_job_flow(flow_id, trigger_type='manual', trigger_user_id=None, input_params=None):
    """
    Execute a job flow (DAG workflow) using the DAG execution engine.

    Args:
        flow_id: Flow ID to execute
        trigger_type: Type of trigger (cron, manual, api)
        trigger_user_id: User ID who triggered the flow
        input_params: Optional input parameters
    """
    from .models import JobFlow
    from .services import DAGExecutionEngine

    try:
        flow = JobFlow.objects.get(pk=flow_id)
    except JobFlow.DoesNotExist:
        logger.error(f'Flow {flow_id} not found')
        return {'status': 'error', 'message': 'Flow not found'}

    logger.info(f'Starting flow {flow.id} ({flow.name})')

    # Use DAG execution engine
    engine = DAGExecutionEngine(
        flow=flow,
        trigger_user_id=trigger_user_id,
        input_params=input_params
    )

    result = engine.execute()

    logger.info(f'Flow {flow.id} completed with status: {result.get("status")}')

    return result


@shared_task
def send_job_alert(job_id, log_id, alert_type):
    """
    Send job alert notification.

    Args:
        job_id: Job ID
        log_id: Log ID
        alert_type: Type of alert (failure, timeout)
    """
    from .models import Job, JobLog, JobAlert
    from .services import AlertService

    try:
        job = Job.objects.get(pk=job_id)
        log = JobLog.objects.get(pk=log_id)
    except (Job.DoesNotExist, JobLog.DoesNotExist):
        logger.error(f'Job or log not found: job_id={job_id}, log_id={log_id}')
        return

    # Create alert record
    if alert_type == 'failure':
        title = f'任务执行失败: {job.name}'
    elif alert_type == 'timeout':
        title = f'任务执行超时: {job.name}'
    else:
        title = f'任务告警: {job.name}'

    alert = JobAlert.objects.create(
        job=job,
        log=log,
        alert_type=alert_type,
        title=title,
        content=log.error_msg or f'任务 {job.name} {alert_type}',
        channels=job.alert_channels or [],
        status='pending',
    )

    # Send alert via configured channels
    try:
        AlertService.send_alert(job, log, alert_type)
        alert.status = 'sent'
        alert.sent_at = timezone.now()
        alert.save()
        logger.info(f'Alert sent for job {job.id}, alert_id: {alert.id}')
    except Exception as e:
        logger.error(f'Failed to send alert for job {job.id}: {e}')
        alert.status = 'pending'
        alert.save()


@shared_task
def sync_schedules():
    """
    Sync all job and flow schedules to Celery Beat.
    Called periodically or after configuration changes.
    """
    from .services import SchedulerService

    result = SchedulerService.sync_all_schedules()
    logger.info(f'Synced schedules: {result}')
    return result


@shared_task
def cleanup_old_logs(days=30):
    """
    Clean up old job logs.

    Args:
        days: Number of days to keep logs
    """
    from .models import JobLog, FlowInstance

    cutoff_date = timezone.now() - timezone.timedelta(days=days)

    # Delete old job logs
    deleted_logs, _ = JobLog.objects.filter(start_time__lt=cutoff_date).delete()

    # Delete old flow instances
    deleted_instances, _ = FlowInstance.objects.filter(start_time__lt=cutoff_date).delete()

    logger.info(f'Cleaned up {deleted_logs} job logs and {deleted_instances} flow instances older than {days} days')

    return {'deleted_logs': deleted_logs, 'deleted_instances': deleted_instances}


@shared_task
def check_running_jobs():
    """
    Check for stuck running jobs and mark them as timeout.
    Called periodically to detect jobs that may have crashed.
    """
    from .models import JobLog

    # Find jobs that have been running for longer than their timeout
    stuck_logs = JobLog.objects.filter(
        status='running',
        start_time__lt=timezone.now() - timezone.timedelta(hours=1)
    ).select_related('job')

    for log in stuck_logs:
        # Check if job has a timeout configured
        if log.job.timeout:
            max_runtime = timezone.timedelta(seconds=log.job.timeout * 2)  # 2x timeout as grace period
            if timezone.now() - log.start_time > max_runtime:
                log.status = 'timeout'
                log.end_time = timezone.now()
                log.error_msg = 'Job marked as timeout due to excessive runtime'
                log.save()
                logger.warning(f'Marked stuck job log {log.id} as timeout')

                # Send timeout alert
                if log.job.alert_on_timeout:
                    send_job_alert.delay(log.job_id, log.id, 'timeout')
