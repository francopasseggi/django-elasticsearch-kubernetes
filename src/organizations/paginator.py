import json
from base64 import b64decode, b64encode
from urllib.parse import urlencode

from rest_framework.exceptions import NotFound
from rest_framework.pagination import BasePagination
from rest_framework.response import Response


class ElasticsearchCursorPagination(BasePagination):
    def __init__(
        self,
        page_size=10,
        max_page_size=100,
        cursor_query_param="cursor",
        page_size_query_param="page_size",
    ):
        self.page_size = page_size
        self.max_page_size = max_page_size
        self.cursor_query_param = cursor_query_param
        self.page_size_query_param = page_size_query_param

    def paginate_queryset(self, queryset, request, view=None):
        self.page_size = self.get_page_size(request)
        if not self.page_size:
            return None

        self.base_url = request.build_absolute_uri().split("?")[0]
        self.request_query_params = request.query_params.copy()

        # Decode the cursor from the request query parameters
        self.cursor = self.decode_cursor(request.query_params.get(self.cursor_query_param))

        # If a cursor exists, use Elasticsearch's search_after for pagination.
        if self.cursor is not None:
            queryset = queryset.extra(search_after=self.cursor)

        # Elasticsearch DSL's Search object uses lazy execution. It doesn't actually
        # execute the query until we try to iterate over it or convert it to a list.
        # Fetch one extra item to determine if there's a next page
        self.page = list(queryset[: self.page_size + 1])

        return self.page[: self.page_size]

    def get_paginated_response(self, data):
        return Response({"next": self.get_next_link(), "results": data})

    def get_next_link(self):
        if len(self.page) <= self.page_size:
            return None

        next_cursor = self.get_next_cursor()
        encoded_cursor = self.encode_cursor(next_cursor)

        self.request_query_params[self.cursor_query_param] = encoded_cursor
        return f"{self.base_url}?{urlencode(self.request_query_params)}"

    def get_next_cursor(self):
        last_item = self.page[-1]
        return [str(value) for value in last_item.meta.sort]

    def encode_cursor(self, cursor):
        return b64encode(json.dumps(cursor).encode("utf-8")).decode("ascii")

    def decode_cursor(self, encoded):
        if encoded is None:
            return None

        try:
            decoded = b64decode(encoded.encode("ascii")).decode("utf-8")
            return json.loads(decoded)
        except (TypeError, ValueError):
            raise NotFound("Invalid cursor")

    def get_page_size(self, request):
        if self.page_size_query_param:
            try:
                return min(
                    int(request.query_params[self.page_size_query_param]), self.max_page_size
                )
            except (KeyError, ValueError):
                pass

        return self.page_size
