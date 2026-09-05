from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    allowed_page_sizes = {20, 50, 100}

    def get_page_size(self, request):
        raw_page_size = request.query_params.get(self.page_size_query_param)
        if raw_page_size is None:
            return self.page_size

        try:
            requested_page_size = int(raw_page_size)
        except (TypeError, ValueError):
            return self.page_size

        if requested_page_size in self.allowed_page_sizes:
            return requested_page_size

        return self.page_size
