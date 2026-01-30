"""
Management command to seed sample report data.
Creates a datasource pointing to the OPS database itself,
and several sample reports that query system data.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.report.models import DataSource, Report


class Command(BaseCommand):
    help = 'Seed sample report data for demonstration'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample report data...')

        # Get database config from settings
        db_config = settings.DATABASES.get('default', {})

        # Create or update the OPS system datasource
        datasource, created = DataSource.objects.update_or_create(
            name='OPS系统数据库',
            defaults={
                'type': 'mysql',
                'host': db_config.get('HOST', 'localhost'),
                'port': int(db_config.get('PORT', 3306)),
                'database_name': db_config.get('NAME', 'ops'),
                'username': db_config.get('USER', 'root'),
                'password': db_config.get('PASSWORD', ''),
                'status': 'active',
            }
        )
        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{action} datasource: {datasource.name}'))

        # Sample reports
        reports_config = [
            {
                'name': '用户统计报表',
                'description': '统计系统用户的活跃状态分布',
                'display_type': 'pie',
                'query_config': {
                    'sql': '''
                        SELECT
                            CASE WHEN is_active = 1 THEN '活跃用户' ELSE '禁用用户' END as status,
                            COUNT(*) as count
                        FROM t_user
                        GROUP BY is_active
                    '''
                },
                'status': 'published',
                'is_public': True,
            },
            {
                'name': '用户列表',
                'description': '系统用户详细信息表格',
                'display_type': 'table',
                'query_config': {
                    'sql': '''
                        SELECT
                            username as 用户名,
                            real_name as 真实姓名,
                            email as 邮箱,
                            phone as 手机号,
                            CASE WHEN is_active = 1 THEN '启用' ELSE '禁用' END as 状态,
                            DATE_FORMAT(created_at, '%Y-%m-%d %H:%i') as 创建时间
                        FROM t_user
                        ORDER BY created_at DESC
                        LIMIT 100
                    '''
                },
                'status': 'published',
                'is_public': True,
            },
            {
                'name': '任务类型分布',
                'description': '按任务类型统计调度任务数量',
                'display_type': 'bar',
                'query_config': {
                    'sql': '''
                        SELECT
                            CASE job_type
                                WHEN 'shell' THEN 'Shell脚本'
                                WHEN 'python' THEN 'Python脚本'
                                WHEN 'http' THEN 'HTTP请求'
                                WHEN 'sql' THEN 'SQL查询'
                                ELSE job_type
                            END as 任务类型,
                            COUNT(*) as 数量
                        FROM t_job
                        GROUP BY job_type
                    '''
                },
                'status': 'published',
                'is_public': True,
            },
            {
                'name': '系统概览指标',
                'description': '展示系统核心指标卡片',
                'display_type': 'card',
                'query_config': {
                    'sql': '''
                        SELECT
                            (SELECT COUNT(*) FROM t_user) as 用户总数,
                            (SELECT COUNT(*) FROM t_user WHERE is_active = 1) as 活跃用户,
                            (SELECT COUNT(*) FROM t_role) as 角色数量,
                            (SELECT COUNT(*) FROM t_job) as 任务数量
                    '''
                },
                'status': 'published',
                'is_public': True,
            },
            {
                'name': '角色权限统计',
                'description': '各角色拥有的权限数量',
                'display_type': 'bar',
                'query_config': {
                    'sql': '''
                        SELECT
                            r.name as 角色名称,
                            COUNT(rp.permission_id) as 权限数量
                        FROM t_role r
                        LEFT JOIN t_role_permissions rp ON r.id = rp.role_id
                        GROUP BY r.id, r.name
                        ORDER BY 权限数量 DESC
                    '''
                },
                'status': 'published',
                'is_public': True,
            },
            {
                'name': '数据源状态',
                'description': '数据源连接状态统计',
                'display_type': 'pie',
                'query_config': {
                    'sql': '''
                        SELECT
                            CASE status
                                WHEN 'active' THEN '正常'
                                WHEN 'inactive' THEN '停用'
                                WHEN 'error' THEN '异常'
                                ELSE status
                            END as 状态,
                            COUNT(*) as 数量
                        FROM t_datasource
                        GROUP BY status
                    '''
                },
                'status': 'published',
                'is_public': True,
            },
            {
                'name': '任务执行趋势',
                'description': '最近7天任务执行数量趋势',
                'display_type': 'line',
                'query_config': {
                    'sql': '''
                        SELECT
                            DATE_FORMAT(start_time, '%m-%d') as 日期,
                            COUNT(*) as 执行次数
                        FROM t_job_log
                        WHERE start_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                        GROUP BY DATE(start_time)
                        ORDER BY DATE(start_time)
                    '''
                },
                'status': 'published',
                'is_public': True,
            },
            {
                'name': '任务执行状态分布',
                'description': '任务执行结果状态统计',
                'display_type': 'pie',
                'query_config': {
                    'sql': '''
                        SELECT
                            CASE status
                                WHEN 'success' THEN '成功'
                                WHEN 'failed' THEN '失败'
                                WHEN 'running' THEN '运行中'
                                WHEN 'timeout' THEN '超时'
                                WHEN 'pending' THEN '等待中'
                                ELSE status
                            END as 状态,
                            COUNT(*) as 数量
                        FROM t_job_log
                        GROUP BY status
                    '''
                },
                'status': 'published',
                'is_public': True,
            },
        ]

        for report_data in reports_config:
            report, created = Report.objects.update_or_create(
                name=report_data['name'],
                defaults={
                    'datasource': datasource,
                    **report_data
                }
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} report: {report.name}'))

        self.stdout.write(self.style.SUCCESS('Sample report data seeded successfully!'))
        self.stdout.write(f'Total datasources: {DataSource.objects.count()}')
        self.stdout.write(f'Total reports: {Report.objects.count()}')
