"""
Custom pagination that allows the client to request page_size via query param.
Allowed values: 5, 10, 15, 20. Default: 10.
"""
from rest_framework.pagination import PageNumberPagination


PAGE_SIZE_CHOICES = (5, 10, 15, 20)
DEFAULT_PAGE_SIZE = 10


class OptionalPageSizePagination(PageNumberPagination):
    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = max(PAGE_SIZE_CHOICES)

    def get_page_size(self, request):
        try:
            size = int(request.query_params.get(self.page_size_query_param, self.page_size))
        except (TypeError, ValueError):
            size = self.page_size
        if size in PAGE_SIZE_CHOICES:
            return size
        return self.page_size



