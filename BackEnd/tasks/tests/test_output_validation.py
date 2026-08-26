"""Tests for output validation: retry logic on GroqModelClient, the fixed
confidence field in agent_runner, and priority/confidence validation in
extraction.py.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "Agent" / "src"))

from agent.agent_runner import _parse_tasks_json
from agent.model_client import GroqModelClient, ModelResponse


def _make_client_with_mocked_groq():
    """Build a GroqModelClient with its underlying groq.Groq client swapped
    for a MagicMock, without needing a real API key or network access.
    """
    with patch("groq.Groq") as mock_groq_cls:
        client = GroqModelClient(api_key="fake-key", max_retries=3, retry_backoff_seconds=0)
        mock_instance = mock_groq_cls.return_value
        client._client = mock_instance
        return client, mock_instance


def test_complete_retries_on_transient_failure_then_succeeds():
    client, mock_groq = _make_client_with_mocked_groq()

    success_response = MagicMock()
    success_response.choices = [MagicMock(message=MagicMock(content='{"tasks": []}'))]

    # Fails twice, succeeds on the third attempt.
    mock_groq.chat.completions.create.side_effect = [
        ConnectionError("network blip"),
        ConnectionError("network blip"),
        success_response,
    ]

    result = client.complete("some prompt")

    assert isinstance(result, ModelResponse)
    assert result.content == '{"tasks": []}'
    assert mock_groq.chat.completions.create.call_count == 3


def test_complete_raises_after_exhausting_all_retries():
    client, mock_groq = _make_client_with_mocked_groq()

    mock_groq.chat.completions.create.side_effect = ConnectionError("always fails")

    with pytest.raises(ConnectionError):
        client.complete("some prompt")

    assert mock_groq.chat.completions.create.call_count == 3  # max_retries


def test_parse_tasks_json_populates_confidence_correctly():
    raw = '{"tasks": [{"title": "Do the thing", "confidence": 0.85}]}'
    tasks = _parse_tasks_json(raw)

    assert len(tasks) == 1
    assert tasks[0]["confidence"] == 0.85


def test_parse_tasks_json_falls_back_to_default_confidence_on_garbage_value():
    raw = '{"tasks": [{"title": "Do the thing", "confidence": "not-a-number"}]}'
    tasks = _parse_tasks_json(raw)

    assert tasks[0]["confidence"] == 0.5


def test_parse_tasks_json_clamps_out_of_range_confidence():
    raw = '{"tasks": [{"title": "Do the thing", "confidence": 5.0}]}'
    tasks = _parse_tasks_json(raw)

    assert tasks[0]["confidence"] == 1.0


def test_validate_priority_rejects_hallucinated_values():
    from BackEnd.tasks.services.extraction import _validate_priority

    assert _validate_priority("high") == "high"
    assert _validate_priority("URGENT") is None  # not one of low/medium/high
    assert _validate_priority(None) is None


def test_validate_confidence_clamps_and_rejects_garbage():
    from BackEnd.tasks.services.extraction import _validate_confidence

    assert _validate_confidence(0.7) == 0.7
    assert _validate_confidence(5.0) == 1.0
    assert _validate_confidence(-2.0) == 0.0
    assert _validate_confidence("not a number") is None


@pytest.mark.django_db
def test_find_latest_task_by_name_degrades_gracefully_on_llm_failure():
    from django.contrib.auth import get_user_model
    from rest_framework.test import APIClient

    User = get_user_model()
    user = User.objects.create_user(username="kate", password="pass12345")

    client = APIClient()
    client.force_authenticate(user=user)

    with patch(
        "BackEnd.tasks.services.name_lookup.extract_person_name",
        side_effect=ConnectionError("groq is down"),
    ):
        response = client.post("/api/tasks/by-message/", {"message": "anything"}, format="json")

    # Must NOT 500 — should degrade to a clear message instead.
    assert response.status_code == 200
    assert response.data["task"] is None