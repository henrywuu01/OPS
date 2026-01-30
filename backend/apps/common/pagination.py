"""
Custom pagination classes.
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """
    Standard pagination with customizable page size.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

    def get_paginated_response(self, data):
        return Response({
            'items': data,
            'total': self.page.paginator.count,
            'page': self.page.number,
            'page_size': self.get_page_size(self.request),
            'pages': self.page.paginator.num_pages,
        })

    def get_paginated_response_schema(self, schema):
        return {
            'type': 'object',
            'properties': {
                'items': schema,
                'total': {'type': 'integer'},
                'page': {'type': 'integer'},
                'page_size': {'type': 'integer'},
                'pages': {'type': 'integer'},
            },
        }
