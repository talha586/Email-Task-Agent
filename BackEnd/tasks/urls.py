from django.urls import path

from .views import TaskDetailView, TaskListView, extract_tasks_view, find_task_by_message_view

urlpatterns = [
    path("extract/", extract_tasks_view, name="extract-tasks"),
    path("by-message/", find_task_by_message_view, name="find-task-by-message"),
    path("", TaskListView.as_view(), name="task-list"),
    path("<int:pk>/", TaskDetailView.as_view(), name="task-detail"),
]