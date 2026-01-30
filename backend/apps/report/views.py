"""
Report views for M3 - Report Center.
"""
import io
import pandas as pd
from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import DataSource, Report, ReportSubscription, ReportFavorite
from .serializers import (
    DataSourceSerializer, DataSourceCreateUpdateSerializer,
    ReportSerializer, ReportCreateUpdateSerializer,
    ReportSubscriptionSerializer, ReportSubscriptionCreateUpdateSerializer,
    ReportFavoriteSerializer
)
from .connectors import get_connector


# DataSource views
class DataSourceListCreateView(generics.ListCreateAPIView):
    """DataSource list and create view."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = DataSource.objects.all()

        # Search filter
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(host__icontains=search)
            )

        # Type filter
        ds_type = self.request.query_params.get('type')
        if ds_type:
            queryset = queryset.filter(type=ds_type)

        # Status filter
        ds_status = self.request.query_params.get('status')
        if ds_status:
            queryset = queryset.filter(status=ds_status)

        return queryset.order_by('name')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DataSourceCreateUpdateSerializer
        return DataSourceSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        datasources = queryset[start:end]
        serializer = DataSourceSerializer(datasources, many=True)

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


class DataSourceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """DataSource detail, update and delete view."""
    permission_classes = [IsAuthenticated]
    queryset = DataSource.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return DataSourceCreateUpdateSerializer
        return DataSourceSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check if datasource is used by any reports
        if instance.reports.exists():
            return Response(
                {'error': '该数据源已被报表使用，无法删除'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)


class DataSourceTestView(APIView):
    """Test datasource connection."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            datasource = DataSource.objects.get(pk=pk)
        except DataSource.DoesNotExist:
            return Response(
                {'error': '数据源不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            connector = get_connector(datasource)
            result = connector.test_connection()

            # Update datasource status
            datasource.last_check_time = timezone.now()
            datasource.last_check_result = result.get('message', '')
            if result.get('success'):
                datasource.status = 'active'
            else:
                datasource.status = 'error'
            datasource.save(update_fields=['last_check_time', 'last_check_result', 'status'])

            return Response(result)
        except Exception as e:
            return Response(
                {'success': False, 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Report views
class ReportListCreateView(generics.ListCreateAPIView):
    """Report list and create view."""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Report.objects.all()

        # Search filter
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        # Datasource filter
        datasource = self.request.query_params.get('datasource')
        if datasource:
            queryset = queryset.filter(datasource_id=datasource)

        # Display type filter
        display_type = self.request.query_params.get('display_type')
        if display_type:
            queryset = queryset.filter(display_type=display_type)

        # Status filter
        report_status = self.request.query_params.get('status')
        if report_status:
            queryset = queryset.filter(status=report_status)

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReportCreateUpdateSerializer
        return ReportSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        start = (page - 1) * page_size
        end = start + page_size

        total = queryset.count()
        reports = queryset[start:end]
        serializer = ReportSerializer(
            reports, many=True,
            context={'request': request}
        )

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })


class ReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Report detail, update and delete view."""
    permission_classes = [IsAuthenticated]
    queryset = Report.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ReportCreateUpdateSerializer
        return ReportSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment view count
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ReportQueryView(APIView):
    """Execute report query and return results."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            report = Report.objects.select_related('datasource').get(pk=pk)
        except Report.DoesNotExist:
            return Response(
                {'error': '报表不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get query parameters
        filters = request.data.get('filters', {})
        page = int(request.data.get('page', 1))
        page_size = int(request.data.get('page_size', 100))

        try:
            connector = get_connector(report.datasource)

            # Build SQL query
            query_config = report.query_config
            sql = query_config.get('sql') or query_config.get('query')

            # Apply filters
            if filters:
                where_clauses = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        values_str = ', '.join([f"'{v}'" for v in value])
                        where_clauses.append(f"{key} IN ({values_str})")
                    elif isinstance(value, dict):
                        if 'start' in value and 'end' in value:
                            where_clauses.append(f"{key} BETWEEN '{value['start']}' AND '{value['end']}'")
                    else:
                        where_clauses.append(f"{key} = '{value}'")

                if where_clauses:
                    sql = f"SELECT * FROM ({sql}) AS t WHERE {' AND '.join(where_clauses)}"

            # Add pagination
            offset = (page - 1) * page_size
            sql = f"SELECT * FROM ({sql}) AS t LIMIT {page_size} OFFSET {offset}"

            result = connector.execute_query(sql)

            if result.get('success'):
                return Response({
                    'success': True,
                    'columns': result.get('columns', []),
                    'data': result.get('data', []),
                    'page': page,
                    'page_size': page_size,
                    'display_type': report.display_type,
                    'display_config': report.display_config,
                    'format_config': report.format_config
                })
            else:
                return Response(
                    {'success': False, 'error': result.get('message')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReportExportView(APIView):
    """Export report data to various formats."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            report = Report.objects.select_related('datasource').get(pk=pk)
        except Report.DoesNotExist:
            return Response(
                {'error': '报表不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        export_format = request.data.get('format', 'excel')
        filters = request.data.get('filters', {})

        try:
            connector = get_connector(report.datasource)

            # Get query SQL
            query_config = report.query_config
            sql = query_config.get('sql') or query_config.get('query')

            result = connector.execute_query(sql)

            if not result.get('success'):
                return Response(
                    {'error': result.get('message')},
                    status=status.HTTP_400_BAD_REQUEST
                )

            data = result.get('data', [])
            columns = result.get('columns', [])

            if export_format == 'excel':
                return self._export_excel(report.name, columns, data)
            elif export_format == 'csv':
                return self._export_csv(report.name, columns, data)
            else:
                return Response(
                    {'error': '不支持的导出格式'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _export_excel(self, name, columns, data):
        df = pd.DataFrame(data, columns=columns)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        output.seek(0)

        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{name}.xlsx"'
        return response

    def _export_csv(self, name, columns, data):
        df = pd.DataFrame(data, columns=columns)
        output = io.StringIO()
        df.to_csv(output, index=False)

        response = HttpResponse(
            output.getvalue(),
            content_type='text/csv'
        )
        response['Content-Disposition'] = f'attachment; filename="{name}.csv"'
        return response


class ReportPublishView(APIView):
    """Publish or unpublish a report."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            report = Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            return Response(
                {'error': '报表不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        action = request.data.get('action', 'publish')

        if action == 'publish':
            report.status = 'published'
            message = '报表已发布'
        elif action == 'unpublish':
            report.status = 'draft'
            message = '报表已取消发布'
        elif action == 'archive':
            report.status = 'archived'
            message = '报表已归档'
        else:
            return Response(
                {'error': '无效的操作'},
                status=status.HTTP_400_BAD_REQUEST
            )

        report.save(update_fields=['status'])
        return Response({'message': message, 'status': report.status})


# Subscription views
class ReportSubscriptionListCreateView(APIView):
    """Report subscription list and create view."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            report = Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            return Response(
                {'error': '报表不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        subscriptions = report.subscriptions.all()
        serializer = ReportSubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data)

    def post(self, request, pk):
        try:
            report = Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            return Response(
                {'error': '报表不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if already subscribed
        if report.subscriptions.filter(user=request.user).exists():
            return Response(
                {'error': '您已订阅该报表'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ReportSubscriptionCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subscription = ReportSubscription.objects.create(
            report=report,
            user=request.user,
            **serializer.validated_data
        )

        return Response(
            ReportSubscriptionSerializer(subscription).data,
            status=status.HTTP_201_CREATED
        )


class ReportSubscriptionDetailView(APIView):
    """Report subscription detail, update and delete view."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, sub_id):
        try:
            subscription = ReportSubscription.objects.get(pk=sub_id, report_id=pk)
        except ReportSubscription.DoesNotExist:
            return Response(
                {'error': '订阅不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ReportSubscriptionSerializer(subscription)
        return Response(serializer.data)

    def put(self, request, pk, sub_id):
        try:
            subscription = ReportSubscription.objects.get(pk=sub_id, report_id=pk)
        except ReportSubscription.DoesNotExist:
            return Response(
                {'error': '订阅不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only allow owner to update
        if subscription.user != request.user:
            return Response(
                {'error': '无权修改'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ReportSubscriptionCreateUpdateSerializer(
            subscription, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        for attr, value in serializer.validated_data.items():
            setattr(subscription, attr, value)
        subscription.save()

        return Response(ReportSubscriptionSerializer(subscription).data)

    def delete(self, request, pk, sub_id):
        try:
            subscription = ReportSubscription.objects.get(pk=sub_id, report_id=pk)
        except ReportSubscription.DoesNotExist:
            return Response(
                {'error': '订阅不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only allow owner to delete
        if subscription.user != request.user:
            return Response(
                {'error': '无权删除'},
                status=status.HTTP_403_FORBIDDEN
            )

        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Favorite views
class ReportFavoriteView(APIView):
    """Toggle report favorite."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            report = Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            return Response(
                {'error': '报表不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        favorite, created = ReportFavorite.objects.get_or_create(
            report=report, user=request.user
        )

        if created:
            return Response({'message': '收藏成功'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': '已收藏'})

    def delete(self, request, pk):
        try:
            favorite = ReportFavorite.objects.get(report_id=pk, user=request.user)
            favorite.delete()
            return Response({'message': '取消收藏成功'})
        except ReportFavorite.DoesNotExist:
            return Response(
                {'error': '未收藏该报表'},
                status=status.HTTP_404_NOT_FOUND
            )


class MyFavoriteReportsView(APIView):
    """List current user's favorite reports."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        favorites = ReportFavorite.objects.filter(
            user=request.user
        ).select_related('report').order_by('-created_at')

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        start = (page - 1) * page_size
        end = start + page_size

        total = favorites.count()
        favorites_page = favorites[start:end]

        reports = [f.report for f in favorites_page]
        serializer = ReportSerializer(
            reports, many=True,
            context={'request': request}
        )

        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })
