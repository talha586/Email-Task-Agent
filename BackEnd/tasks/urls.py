from django.urls import path

from .views import TaskDetailView, TaskListView, extract_tasks_view

urlpatterns = [
    path("extract/", extract_tasks_view, name="extract-tasks"),
    path("", TaskListView.as_view(), name="task-list"),
    path("<int:pk>/", TaskDetailView.as_view(), name="task-detail"),
]