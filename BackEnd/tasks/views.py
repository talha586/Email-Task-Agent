from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response

from .models import Task
from .serializers import TaskSerializer
from .services import run_extraction


@api_view(["GET"])
def extract_tasks_view(request):
    """GET /api/tasks/extract/ — scan the inbox, extract tasks, and save
    both the fetched emails and the extracted tasks to the database.

    Every task created here is owned by request.user (the authenticated
    caller) — ownership is never taken from anything the client sends.

    Optional query param: ?limit=10
    """
    limit = int(request.query_params.get("limit", 10))
    data = run_extraction(user=request.user, limit=limit)
    return Response(data)


class TaskListView(ListAPIView):
    """GET /api/tasks/ — lists ONLY the authenticated user's own tasks."""

    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user)


class TaskDetailView(RetrieveUpdateDestroyAPIView):
    """GET/PATCH/PUT/DELETE /api/tasks/<id>/ — scoped to the requesting
    user's own tasks. Filtering the queryset (not just checking auth) is
    what actually stops user B from reading/editing/deleting user A's
    task by guessing an id — DRF returns a plain 404 for someone else's
    task id, so its existence isn't even revealed.
    """

    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user)