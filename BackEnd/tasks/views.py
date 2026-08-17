
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response

from .models import Task
from .serializers import TaskSerializer
from .services import run_extraction


@api_view(["GET"])
def extract_tasks_view(request):
    """GET /api/tasks/extract/ — scan the inbox, extract tasks, and save both
    the fetched emails and the extracted tasks to the database.

    Optional query param: ?limit=10
    """
    limit = int(request.query_params.get("limit", 10))
    data = run_extraction(limit=limit)
    return Response(data)


class TaskListView(ListAPIView):
    """GET /api/tasks/ — list all saved tasks."""

    queryset = Task.objects.all()
    serializer_class = TaskSerializer


class TaskDetailView(RetrieveUpdateDestroyAPIView):
    """GET/PATCH/PUT/DELETE /api/tasks/<id>/ — inspect, edit, or remove one task."""

    queryset = Task.objects.all()
    serializer_class = TaskSerializer