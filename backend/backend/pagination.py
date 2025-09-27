from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination


class CustomPagination(LimitOffsetPagination):
    max_limit = 200
    default_limit = 20

    # def get_paginated_response(self, data, count, **kwargs):
    #     response_data = {
    #         "next_page": self.get_next_link(),
    #         "prev_page": self.get_previous_link(),
    #         "count": count,
    #         "result": data,
    #     }

    #     response_data.update(**kwargs)
    #     return Response(success_payload(response_data))
