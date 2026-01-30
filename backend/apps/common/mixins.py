"""
View mixins for performance and common functionality.
"""
from rest_framework import status
from rest_framework.response import Response


class OptimizedQueryMixin:
    """
    Mixin for optimizing database queries with select_related and prefetch_related.

    Usage:
        class MyViewSet(OptimizedQueryMixin, viewsets.ModelViewSet):
            queryset = MyModel.objects.all()
            select_related_fields = ['author', 'category']
            prefetch_related_fields = ['tags', 'comments']
    """

    select_related_fields = []
    prefetch_related_fields = []

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.select_related_fields:
            queryset = queryset.select_related(*self.select_related_fields)

        if self.prefetch_related_fields:
            queryset = queryset.prefetch_related(*self.prefetch_related_fields)

        return queryset


class BulkOperationMixin:
    """
    Mixin for bulk create/update/delete operations.

    Usage:
        class MyViewSet(BulkOperationMixin, viewsets.ModelViewSet):
            ...

    Endpoints:
        POST /bulk-create/
        PATCH /bulk-update/
        DELETE /bulk-delete/
    """

    def bulk_create(self, request, *args, **kwargs):
        """Bulk create objects."""
        items = request.data.get('items', [])
        if not items:
            return Response({'error': 'No items provided'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=items, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_bulk_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_bulk_create(self, serializer):
        serializer.save()

    def bulk_update(self, request, *args, **kwargs):
        """Bulk update objects."""
        items = request.data.get('items', [])
        if not items:
            return Response({'error': 'No items provided'}, status=status.HTTP_400_BAD_REQUEST)

        updated = []
        for item in items:
            pk = item.get('id')
            if not pk:
                continue
            try:
                instance = self.get_queryset().get(pk=pk)
                serializer = self.get_serializer(instance, data=item, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                updated.append(serializer.data)
            except self.get_queryset().model.DoesNotExist:
                pass

        return Response({'updated': updated})

    def bulk_delete(self, request, *args, **kwargs):
        """Bulk delete objects."""
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'error': 'No IDs provided'}, status=status.HTTP_400_BAD_REQUEST)

        deleted_count = self.get_queryset().filter(pk__in=ids).delete()[0]
        return Response({'deleted': deleted_count})


class SoftDeleteMixin:
    """
    Mixin for soft delete functionality.
    Requires model to have 'is_deleted' and 'deleted_at' fields.

    Usage:
        class MyViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
            ...
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter out soft-deleted records by default
        if hasattr(queryset.model, 'is_deleted'):
            queryset = queryset.filter(is_deleted=False)
        return queryset

    def perform_destroy(self, instance):
        """Soft delete instead of hard delete."""
        from django.utils import timezone
        if hasattr(instance, 'is_deleted'):
            instance.is_deleted = True
            instance.deleted_at = timezone.now()
            instance.save(update_fields=['is_deleted', 'deleted_at'])
        else:
            instance.delete()


class AuditMixin:
    """
    Mixin to automatically record audit information.
    Sets created_by and updated_by fields.

    Usage:
        class MyViewSet(AuditMixin, viewsets.ModelViewSet):
            ...
    """

    def perform_create(self, serializer):
        if hasattr(serializer.Meta.model, 'created_by'):
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()

    def perform_update(self, serializer):
        if hasattr(serializer.Meta.model, 'updated_by'):
            serializer.save(updated_by=self.request.user)
        else:
            serializer.save()


class ExportMixin:
    """
    Mixin for exporting data to Excel/CSV.

    Usage:
        class MyViewSet(ExportMixin, viewsets.ModelViewSet):
            export_fields = ['id', 'name', 'created_at']
            export_headers = {'id': 'ID', 'name': '名称', 'created_at': '创建时间'}
    """

    export_fields = []
    export_headers = {}

    def export(self, request, *args, **kwargs):
        """Export data to Excel or CSV."""
        import io
        import pandas as pd
        from django.http import HttpResponse

        format_type = request.query_params.get('format', 'xlsx')
        queryset = self.filter_queryset(self.get_queryset())

        # Get data
        fields = self.export_fields or [f.name for f in queryset.model._meta.fields]
        data = list(queryset.values(*fields))

        # Create DataFrame
        df = pd.DataFrame(data)

        # Rename columns
        if self.export_headers:
            df = df.rename(columns=self.export_headers)

        # Generate file
        output = io.BytesIO()

        if format_type == 'csv':
            df.to_csv(output, index=False, encoding='utf-8-sig')
            content_type = 'text/csv'
            ext = 'csv'
        else:
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Data')
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            ext = 'xlsx'

        output.seek(0)
        response = HttpResponse(output.getvalue(), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="export.{ext}"'
        return response


class SearchMixin:
    """
    Mixin for full-text search across multiple fields.

    Usage:
        class MyViewSet(SearchMixin, viewsets.ModelViewSet):
            search_fields = ['name', 'description', 'code']
    """

    search_fields = []
    search_param = 'search'

    def get_queryset(self):
        queryset = super().get_queryset()
        search_term = self.request.query_params.get(self.search_param)

        if search_term and self.search_fields:
            from django.db.models import Q
            query = Q()
            for field in self.search_fields:
                query |= Q(**{f'{field}__icontains': search_term})
            queryset = queryset.filter(query)

        return queryset
