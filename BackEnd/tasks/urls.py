from django.urls import path

from .views import extract_tasks_view

urlpatterns = [
    path("extract/", extract_tasks_view, name="extract-tasks"),
]