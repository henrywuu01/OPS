"""
Configuration services for dynamic table operations.
"""
from typing import Dict, List, Any, Optional
from django.db import connection
from django.utils import timezone
from .models import MetaTable, ConfigHistory


class DynamicTableService:
    """Service for dynamic config table operations."""

    @staticmethod
    def get_table_name(meta_table: MetaTable) -> str:
        """Get the actual database table name."""
        return f't_cfg_{meta_table.name}'

    @staticmethod
    def create_dynamic_table(meta_table: MetaTable) -> bool:
        """Create a dynamic table based on meta table definition."""
        table_name = DynamicTableService.get_table_name(meta_table)
        fields = meta_table.field_config or []

        sql_fields = ['id BIGINT AUTO_INCREMENT PRIMARY KEY']

        for field in fields:
            field_name = field.get('name')
            field_type = field.get('type')
            required = field.get('required', False)
            default = field.get('default')

            sql_type = DynamicTableService._get_sql_type(field_type, field)
            null_clause = 'NOT NULL' if required else 'NULL'
            default_clause = f"DEFAULT '{default}'" if default else ''

            sql_fields.append(f'{field_name} {sql_type} {null_clause} {default_clause}')

        # Add audit fields
        sql_fields.extend([
            'created_at DATETIME DEFAULT CURRENT_TIMESTAMP',
            'updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
            'created_by BIGINT NULL',
            'updated_by BIGINT NULL',
            'is_deleted TINYINT DEFAULT 0'
        ])

        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join(sql_fields)}
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """

        with connection.cursor() as cursor:
            cursor.execute(create_sql)

        return True

    @staticmethod
    def _get_sql_type(field_type: str, field_def: dict) -> str:
        """Convert field type to SQL type."""
        type_mapping = {
            'string': lambda f: f"VARCHAR({f.get('max_length', 255)})",
            'text': lambda f: 'TEXT',
            'integer': lambda f: 'BIGINT',
            'decimal': lambda f: f"DECIMAL({f.get('max_digits', 10)},{f.get('decimal_places', 2)})",
            'boolean': lambda f: 'TINYINT(1)',
            'date': lambda f: 'DATE',
            'datetime': lambda f: 'DATETIME',
            'json': lambda f: 'JSON',
            'image': lambda f: 'VARCHAR(500)',
            'file': lambda f: 'VARCHAR(500)',
            'richtext': lambda f: 'LONGTEXT',
            'select': lambda f: f"VARCHAR({f.get('max_length', 50)})",
            'foreign_key': lambda f: 'BIGINT',
        }
        return type_mapping.get(field_type, lambda f: 'VARCHAR(255)')(field_def)

    @staticmethod
    def list_records(meta_table: MetaTable, filters: Dict = None,
                     page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """List records from dynamic table."""
        table_name = DynamicTableService.get_table_name(meta_table)
        filters = filters or {}

        where_clauses = ['is_deleted = 0']
        params = []

        for key, value in filters.items():
            if isinstance(value, list):
                placeholders = ', '.join(['%s'] * len(value))
                where_clauses.append(f'{key} IN ({placeholders})')
                params.extend(value)
            elif isinstance(value, dict):
                if 'start' in value:
                    where_clauses.append(f'{key} >= %s')
                    params.append(value['start'])
                if 'end' in value:
                    where_clauses.append(f'{key} <= %s')
                    params.append(value['end'])
                if 'like' in value:
                    where_clauses.append(f'{key} LIKE %s')
                    params.append(f'%{value["like"]}%')
            else:
                where_clauses.append(f'{key} = %s')
                params.append(value)

        where_sql = ' AND '.join(where_clauses)
        offset = (page - 1) * page_size

        with connection.cursor() as cursor:
            # Count total
            cursor.execute(f'SELECT COUNT(*) FROM {table_name} WHERE {where_sql}', params)
            total = cursor.fetchone()[0]

            # Get data
            cursor.execute(
                f'SELECT * FROM {table_name} WHERE {where_sql} ORDER BY id DESC LIMIT %s OFFSET %s',
                params + [page_size, offset]
            )
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': [dict(zip(columns, row)) for row in rows]
        }

    @staticmethod
    def get_record(meta_table: MetaTable, record_id: int) -> Optional[Dict]:
        """Get a single record by ID."""
        table_name = DynamicTableService.get_table_name(meta_table)

        with connection.cursor() as cursor:
            cursor.execute(
                f'SELECT * FROM {table_name} WHERE id = %s AND is_deleted = 0',
                [record_id]
            )
            row = cursor.fetchone()
            if not row:
                return None
            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row))

    @staticmethod
    def create_record(meta_table: MetaTable, data: Dict, user_id: int) -> Dict:
        """Create a new record."""
        table_name = DynamicTableService.get_table_name(meta_table)
        data['created_by'] = user_id
        data['updated_by'] = user_id

        fields = list(data.keys())
        values = list(data.values())
        placeholders = ', '.join(['%s'] * len(values))

        with connection.cursor() as cursor:
            cursor.execute(
                f'INSERT INTO {table_name} ({", ".join(fields)}) VALUES ({placeholders})',
                values
            )
            record_id = cursor.lastrowid

        record = DynamicTableService.get_record(meta_table, record_id)

        # Record history
        if meta_table.need_history:
            DynamicTableService._record_history(
                meta_table.name, record_id, 'insert',
                None, record, user_id
            )

        return record

    @staticmethod
    def update_record(meta_table: MetaTable, record_id: int,
                      data: Dict, user_id: int, remark: str = None) -> Optional[Dict]:
        """Update an existing record."""
        table_name = DynamicTableService.get_table_name(meta_table)

        # Get old data
        old_record = DynamicTableService.get_record(meta_table, record_id)
        if not old_record:
            return None

        data['updated_by'] = user_id

        set_clauses = [f'{k} = %s' for k in data.keys()]
        values = list(data.values()) + [record_id]

        with connection.cursor() as cursor:
            cursor.execute(
                f'UPDATE {table_name} SET {", ".join(set_clauses)} WHERE id = %s',
                values
            )

        new_record = DynamicTableService.get_record(meta_table, record_id)

        # Record history
        if meta_table.need_history:
            changes = DynamicTableService._compute_changes(old_record, new_record)
            DynamicTableService._record_history(
                meta_table.name, record_id, 'update',
                old_record, new_record, user_id, changes, remark
            )

        return new_record

    @staticmethod
    def delete_record(meta_table: MetaTable, record_id: int, user_id: int) -> bool:
        """Soft delete a record."""
        table_name = DynamicTableService.get_table_name(meta_table)

        old_record = DynamicTableService.get_record(meta_table, record_id)
        if not old_record:
            return False

        with connection.cursor() as cursor:
            cursor.execute(
                f'UPDATE {table_name} SET is_deleted = 1, updated_by = %s WHERE id = %s',
                [user_id, record_id]
            )

        if meta_table.need_history:
            DynamicTableService._record_history(
                meta_table.name, record_id, 'delete',
                old_record, None, user_id
            )

        return True

    @staticmethod
    def rollback_record(meta_table: MetaTable, record_id: int,
                        version: int, user_id: int) -> Optional[Dict]:
        """Rollback a record to a specific version."""
        history = ConfigHistory.objects.filter(
            table_name=meta_table.name,
            record_id=record_id,
            version=version
        ).first()

        if not history:
            return None

        target_data = history.old_data if history.action == 'update' else history.new_data
        if not target_data:
            return None

        table_name = DynamicTableService.get_table_name(meta_table)
        old_record = DynamicTableService.get_record(meta_table, record_id)

        # Update with historical data
        target_data.pop('id', None)
        target_data.pop('created_at', None)
        target_data.pop('updated_at', None)
        target_data.pop('is_deleted', None)
        target_data['updated_by'] = user_id

        set_clauses = [f'{k} = %s' for k in target_data.keys()]
        values = list(target_data.values()) + [record_id]

        with connection.cursor() as cursor:
            cursor.execute(
                f'UPDATE {table_name} SET {", ".join(set_clauses)} WHERE id = %s',
                values
            )

        new_record = DynamicTableService.get_record(meta_table, record_id)

        if meta_table.need_history:
            DynamicTableService._record_history(
                meta_table.name, record_id, 'rollback',
                old_record, new_record, user_id,
                remark=f'回滚到版本 {version}'
            )

        return new_record

    @staticmethod
    def get_record_history(meta_table: MetaTable, record_id: int) -> List[Dict]:
        """Get change history for a record."""
        histories = ConfigHistory.objects.filter(
            table_name=meta_table.name,
            record_id=record_id
        ).order_by('-version')

        return list(histories.values())

    @staticmethod
    def compare_versions(meta_table: MetaTable, record_id: int,
                         version1: int, version2: int) -> Dict:
        """Compare two versions of a record."""
        h1 = ConfigHistory.objects.filter(
            table_name=meta_table.name, record_id=record_id, version=version1
        ).first()
        h2 = ConfigHistory.objects.filter(
            table_name=meta_table.name, record_id=record_id, version=version2
        ).first()

        if not h1 or not h2:
            return {'error': 'Version not found'}

        data1 = h1.new_data or h1.old_data or {}
        data2 = h2.new_data or h2.old_data or {}

        changes = DynamicTableService._compute_changes(data1, data2)

        return {
            'version1': version1,
            'version2': version2,
            'changes': changes
        }

    @staticmethod
    def _record_history(table_name: str, record_id: int, action: str,
                        old_data: Dict, new_data: Dict, user_id: int,
                        changes: Dict = None, remark: str = None):
        """Record change history."""
        # Get current max version
        last_history = ConfigHistory.objects.filter(
            table_name=table_name, record_id=record_id
        ).order_by('-version').first()
        version = (last_history.version + 1) if last_history else 1

        ConfigHistory.objects.create(
            table_name=table_name,
            record_id=record_id,
            action=action,
            version=version,
            old_data=old_data,
            new_data=new_data,
            changes=changes,
            remark=remark,
            operator_id=user_id
        )

    @staticmethod
    def _compute_changes(old_data: Dict, new_data: Dict) -> Dict:
        """Compute field-level changes between two records."""
        changes = {}
        all_keys = set((old_data or {}).keys()) | set((new_data or {}).keys())

        for key in all_keys:
            if key in ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']:
                continue

            old_val = (old_data or {}).get(key)
            new_val = (new_data or {}).get(key)

            if old_val != new_val:
                changes[key] = {
                    'old': old_val,
                    'new': new_val
                }

        return changes
