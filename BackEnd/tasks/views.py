from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services import run_extraction


@api_view(["GET"])
def extract_tasks_view(request):
    """GET /api/tasks/extract/ — scan the inbox and return extracted tasks.

    Optional query param: ?limit=10
    """
    limit = int(request.query_params.get("limit", 10))
    data = run_extraction(limit=limit)
    return Response(data)