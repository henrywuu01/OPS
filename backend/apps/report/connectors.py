"""
Database connectors for various data sources.
"""
import json
from typing import Dict, List, Any, Optional
from contextlib import contextmanager


class BaseConnector:
    """Base class for database connectors."""

    def __init__(self, config: Dict[str, Any]):
        self.host = config.get('host')
        self.port = config.get('port')
        self.database = config.get('database_name')
        self.username = config.get('username')
        self.password = config.get('password')
        self.extra_config = config.get('extra_config', {})

    def test_connection(self) -> Dict[str, Any]:
        """Test database connection."""
        raise NotImplementedError

    def execute_query(self, sql: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute SQL query and return results."""
        raise NotImplementedError

    def close(self):
        """Close the connection."""
        pass


class MySQLConnector(BaseConnector):
    """MySQL database connector."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connection = None

    def _get_connection(self):
        if self.connection is None:
            import MySQLdb
            self.connection = MySQLdb.connect(
                host=self.host,
                port=self.port or 3306,
                db=self.database,
                user=self.username,
                passwd=self.password,
                charset=self.extra_config.get('charset', 'utf8mb4'),
                connect_timeout=10
            )
        return self.connection

    def test_connection(self) -> Dict[str, Any]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.close()
            return {'success': True, 'message': '连接成功'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
        finally:
            self.close()

    def execute_query(self, sql: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params or {})

            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()

            return {
                'success': True,
                'columns': columns,
                'data': [dict(zip(columns, row)) for row in rows],
                'row_count': len(rows)
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}
        finally:
            self.close()

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None


class PostgreSQLConnector(BaseConnector):
    """PostgreSQL database connector."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connection = None

    def _get_connection(self):
        if self.connection is None:
            import psycopg2
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port or 5432,
                dbname=self.database,
                user=self.username,
                password=self.password,
                connect_timeout=10
            )
        return self.connection

    def test_connection(self) -> Dict[str, Any]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.close()
            return {'success': True, 'message': '连接成功'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
        finally:
            self.close()

    def execute_query(self, sql: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)

            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()

            return {
                'success': True,
                'columns': columns,
                'data': [dict(zip(columns, row)) for row in rows],
                'row_count': len(rows)
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}
        finally:
            self.close()

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None


class ClickHouseConnector(BaseConnector):
    """ClickHouse database connector."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = None

    def _get_client(self):
        if self.client is None:
            from clickhouse_driver import Client
            self.client = Client(
                host=self.host,
                port=self.port or 9000,
                database=self.database,
                user=self.username or 'default',
                password=self.password or '',
                connect_timeout=10
            )
        return self.client

    def test_connection(self) -> Dict[str, Any]:
        try:
            client = self._get_client()
            client.execute('SELECT 1')
            return {'success': True, 'message': '连接成功'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def execute_query(self, sql: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        try:
            client = self._get_client()
            result = client.execute(sql, params or {}, with_column_types=True)

            data, columns_with_types = result if len(result) == 2 else (result, [])
            columns = [col[0] for col in columns_with_types]

            return {
                'success': True,
                'columns': columns,
                'data': [dict(zip(columns, row)) for row in data],
                'row_count': len(data)
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}


class ElasticsearchConnector(BaseConnector):
    """Elasticsearch connector."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = None

    def _get_client(self):
        if self.client is None:
            from elasticsearch import Elasticsearch
            self.client = Elasticsearch(
                hosts=[f"{self.host}:{self.port or 9200}"],
                http_auth=(self.username, self.password) if self.username else None,
                timeout=10
            )
        return self.client

    def test_connection(self) -> Dict[str, Any]:
        try:
            client = self._get_client()
            if client.ping():
                return {'success': True, 'message': '连接成功'}
            else:
                return {'success': False, 'message': '无法连接到Elasticsearch'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def execute_query(self, sql: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        try:
            client = self._get_client()
            # Parse query as JSON for Elasticsearch DSL
            query = json.loads(sql) if isinstance(sql, str) else sql
            index = params.get('index', '*') if params else '*'

            result = client.search(index=index, body=query)
            hits = result.get('hits', {}).get('hits', [])

            data = [hit.get('_source', {}) for hit in hits]
            columns = list(data[0].keys()) if data else []

            return {
                'success': True,
                'columns': columns,
                'data': data,
                'row_count': len(data),
                'total': result.get('hits', {}).get('total', {}).get('value', len(data))
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}


class MongoDBConnector(BaseConnector):
    """MongoDB connector."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = None

    def _get_client(self):
        if self.client is None:
            from pymongo import MongoClient
            uri = f"mongodb://{self.username}:{self.password}@{self.host}:{self.port or 27017}"
            self.client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        return self.client

    def test_connection(self) -> Dict[str, Any]:
        try:
            client = self._get_client()
            client.server_info()
            return {'success': True, 'message': '连接成功'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def execute_query(self, sql: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        try:
            client = self._get_client()
            db = client[self.database]

            # Parse query as JSON
            query_config = json.loads(sql) if isinstance(sql, str) else sql
            collection_name = query_config.get('collection')
            filter_query = query_config.get('filter', {})
            projection = query_config.get('projection')
            limit = query_config.get('limit', 100)

            collection = db[collection_name]
            cursor = collection.find(filter_query, projection).limit(limit)

            data = list(cursor)
            # Convert ObjectId to string
            for doc in data:
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])

            columns = list(data[0].keys()) if data else []

            return {
                'success': True,
                'columns': columns,
                'data': data,
                'row_count': len(data)
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}


def get_connector(datasource) -> BaseConnector:
    """Factory function to get the appropriate connector for a datasource."""
    config = {
        'host': datasource.host,
        'port': datasource.port,
        'database_name': datasource.database_name,
        'username': datasource.username,
        'password': datasource.password,
        'extra_config': datasource.extra_config or {}
    }

    connectors = {
        'mysql': MySQLConnector,
        'postgresql': PostgreSQLConnector,
        'clickhouse': ClickHouseConnector,
        'elasticsearch': ElasticsearchConnector,
        'mongodb': MongoDBConnector,
    }

    connector_class = connectors.get(datasource.type)
    if not connector_class:
        raise ValueError(f'Unsupported datasource type: {datasource.type}')

    return connector_class(config)
