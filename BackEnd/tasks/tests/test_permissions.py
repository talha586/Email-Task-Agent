"""Regression tests for Error-1: the API must require authentication, and
must never let one authenticated user read, edit, or delete another
user's tasks.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from BackEnd.tasks.models import Task

User = get_user_model()


@pytest.mark.django_db
def test_task_list_requires_authentication():
    """No token, no access — an anonymous request must be rejected."""
    client = APIClient()

    response = client.get("/api/tasks/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_user_only_sees_their_own_tasks():
    """Login alone isn't enough — the queryset filter is what actually
    stops user B from seeing user A's tasks in the list endpoint.
    """
    user_a = User.objects.create_user(username="alice", password="pass12345")
    user_b = User.objects.create_user(username="bob", password="pass12345")

    Task.objects.create(owner=user_a, title="Alice's private task")
    Task.objects.create(owner=user_b, title="Bob's private task")

    client = APIClient()
    client.force_authenticate(user=user_a)

    response = client.get("/api/tasks/")

    assert response.status_code == 200
    titles = [task["title"] for task in response.data]
    assert titles == ["Alice's private task"]


@pytest.mark.django_db
def test_user_cannot_read_or_delete_another_users_task():
    """Guessing another user's task id must return 404 (not the task's
    data, and not a 403 that would even confirm the id exists).
    """
    user_a = User.objects.create_user(username="alice2", password="pass12345")
    user_b = User.objects.create_user(username="bob2", password="pass12345")

    private_task = Task.objects.create(owner=user_a, title="Alice's secret task")

    client = APIClient()
    client.force_authenticate(user=user_b)

    read_response = client.get(f"/api/tasks/{private_task.id}/")
    delete_response = client.delete(f"/api/tasks/{private_task.id}/")

    assert read_response.status_code == 404
    assert delete_response.status_code == 404
    # And the delete attempt must not have actually worked.
    assert Task.objects.filter(id=private_task.id).exists()