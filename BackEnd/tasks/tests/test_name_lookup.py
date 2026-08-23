"""Tests for the message-bar name-lookup feature: extract a name from a
message via the (mocked) Agent, check the DB first, and only fall back to
a live (mocked) Gmail fetch on a miss.
"""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from BackEnd.tasks.models import Task

User = get_user_model()


@pytest.mark.django_db
def test_db_hit_returns_immediately_without_a_live_fetch():
    """The fast path: if a matching task already exists, no Gmail call
    should happen at all.
    """
    user = User.objects.create_user(username="erin", password="pass12345")
    Task.objects.create(owner=user, title="Older task", sender="Sarah Khan <sarah@x.com>")
    newest = Task.objects.create(owner=user, title="Newer task", sender="Sarah Khan <sarah@x.com>")

    client = APIClient()
    client.force_authenticate(user=user)

    with patch("BackEnd.tasks.services.name_lookup.extract_person_name", return_value="Sarah"), patch(
        "BackEnd.tasks.services.name_lookup.run_extraction"
    ) as mock_run_extraction:
        response = client.post(
            "/api/tasks/by-message/", {"message": "what did sarah ask me to do"}, format="json"
        )

    assert response.status_code == 200
    assert response.data["task"]["id"] == newest.id
    mock_run_extraction.assert_not_called()


@pytest.mark.django_db
def test_db_miss_falls_back_to_a_live_scoped_fetch():
    """Nothing on file yet for this name — should trigger run_extraction()
    scoped to that sender, and return what it finds.
    """
    user = User.objects.create_user(username="ivan", password="pass12345")

    def fake_run_extraction(user, limit=10, sender_filter=None):
        # Simulate the live fetch actually creating a Task, as the real
        # pipeline would after a successful Gmail fetch + extraction.
        assert sender_filter == "Priya"
        assert limit == 1
        Task.objects.create(owner=user, title="Send the deck", sender="Priya <priya@x.com>")
        return {"messages_fetched": 1, "results": [], "total_tasks": 1}

    client = APIClient()
    client.force_authenticate(user=user)

    with patch("BackEnd.tasks.services.name_lookup.extract_person_name", return_value="Priya"), patch(
        "BackEnd.tasks.services.name_lookup.run_extraction", side_effect=fake_run_extraction
    ) as mock_run_extraction:
        response = client.post(
            "/api/tasks/by-message/", {"message": "what did priya send me"}, format="json"
        )

    assert response.status_code == 200
    assert response.data["task"]["title"] == "Send the deck"
    mock_run_extraction.assert_called_once()


@pytest.mark.django_db
def test_db_miss_and_live_fetch_also_finds_nothing():
    user = User.objects.create_user(username="jack", password="pass12345")

    client = APIClient()
    client.force_authenticate(user=user)

    with patch("BackEnd.tasks.services.name_lookup.extract_person_name", return_value="Nobody"), patch(
        "BackEnd.tasks.services.name_lookup.run_extraction", return_value={"messages_fetched": 0}
    ):
        response = client.post("/api/tasks/by-message/", {"message": "nobody's task"}, format="json")

    assert response.status_code == 200
    assert response.data["task"] is None
    assert "Nobody" in response.data["message"]


@pytest.mark.django_db
def test_find_task_by_message_does_not_leak_another_users_tasks():
    """Isolation must hold on both the fast path AND the live-fetch path."""
    user_a = User.objects.create_user(username="frank", password="pass12345")
    user_b = User.objects.create_user(username="grace", password="pass12345")
    Task.objects.create(owner=user_a, title="Frank's task from sarah", sender="Sarah <sarah@x.com>")

    client = APIClient()
    client.force_authenticate(user=user_b)

    with patch("BackEnd.tasks.services.name_lookup.extract_person_name", return_value="Sarah"), patch(
        "BackEnd.tasks.services.name_lookup.run_extraction", return_value={"messages_fetched": 0}
    ):
        response = client.post("/api/tasks/by-message/", {"message": "sarah's task"}, format="json")

    assert response.status_code == 200
    assert response.data["task"] is None


@pytest.mark.django_db
def test_find_task_by_message_handles_no_name_found():
    user = User.objects.create_user(username="henry", password="pass12345")

    client = APIClient()
    client.force_authenticate(user=user)

    with patch("BackEnd.tasks.services.name_lookup.extract_person_name", return_value=None):
        response = client.post("/api/tasks/by-message/", {"message": "show me everything"}, format="json")

    assert response.status_code == 200
    assert response.data["name"] is None
    assert response.data["task"] is None