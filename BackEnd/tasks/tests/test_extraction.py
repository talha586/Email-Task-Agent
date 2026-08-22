"""Regression tests for Error-2: the KV memory must be keyed per message
(and per user), not per thread — otherwise a genuinely new reply in an
already-seen thread gets thrown away instead of creating its task.
"""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model

from BackEnd.tasks.models import Task, ThreadMemory
from BackEnd.tasks.services.extraction import _memory_key, run_extraction

User = get_user_model()


def _fake_message(message_id, subject="Regarding Tasks", body="", references=""):
    return {
        "message_id": message_id,
        "in_reply_to": "",
        "references": references,
        "subject": subject,
        "from": "thefamilyguy138@gmail.com",
        "date": "Thu, 13 Aug 2026 18:35:39 +0500",
        "body": body,
    }


@pytest.mark.django_db
def test_memory_key_is_scoped_per_user_and_per_message():
    """Same message_id, different users -> different keys. This is what
    stops one user's scan from ever reusing another user's cached tasks.
    """
    message = _fake_message("<abc123@mail.gmail.com>")

    key_for_user_1 = _memory_key(1, message)
    key_for_user_2 = _memory_key(2, message)

    assert key_for_user_1 != key_for_user_2
    assert "abc123" in key_for_user_1


@pytest.mark.django_db
def test_new_reply_in_an_already_seen_thread_still_creates_a_task():
    """The actual bug report: a reply saying 'submit the expense report by
    the 25th' in an old thread was never created, because the OLD code
    keyed memory by thread root, so the whole thread looked 'done' after
    the first message in it was processed.
    """
    user = User.objects.create_user(username="carol", password="pass12345")

    original_message = _fake_message(
        "<original@mail.gmail.com>", references="", body="Let's discuss the budget."
    )
    reply_message = _fake_message(
        "<reply@mail.gmail.com>",
        subject="Re: Regarding Tasks",
        references="<original@mail.gmail.com>",  # same thread as original_message
        body="Please submit the expense report by the 25th.",
    )

    with patch("BackEnd.tasks.services.extraction.fetch_email_data") as mock_fetch, patch(
        "BackEnd.tasks.services.extraction.extract_tasks"
    ) as mock_extract:

        # First scan: only the original message, no action items in it.
        mock_fetch.return_value = [original_message]
        mock_extract.return_value = []
        run_extraction(user=user, limit=10)

        # Second scan: the thread now has a NEW reply with a real task.
        mock_fetch.return_value = [reply_message]
        mock_extract.return_value = [
            {
                "title": "Submit expense report",
                "description": "Submit the expense report by the 25th.",
                "due_date": "2026-08-25",
                "priority": "high",
                "confidence": 0.9,
            }
        ]
        result = run_extraction(user=user, limit=10)

    assert result["total_tasks"] == 1
    assert Task.objects.filter(owner=user, title="Submit expense report").exists()
    # Two distinct messages -> two distinct memory entries, even though
    # they belong to the same thread.
    assert ThreadMemory.objects.count() == 2


@pytest.mark.django_db
def test_rescanning_the_same_message_does_not_duplicate_tasks():
    """A message already processed for this user should be skipped on the
    next scan — because it's the same message, not because of its thread.
    """
    user = User.objects.create_user(username="dave", password="pass12345")
    message = _fake_message("<same-message@mail.gmail.com>")

    with patch("BackEnd.tasks.services.extraction.fetch_email_data") as mock_fetch, patch(
        "BackEnd.tasks.services.extraction.extract_tasks"
    ) as mock_extract:

        mock_fetch.return_value = [message]
        mock_extract.return_value = [
            {
                "title": "Reply to client",
                "description": "",
                "due_date": None,
                "priority": "medium",
                "confidence": 0.7,
            }
        ]

        first_result = run_extraction(user=user, limit=10)
        second_result = run_extraction(user=user, limit=10)

    assert first_result["total_tasks"] == 1
    assert second_result["results"][0]["from_memory"] is True
    assert Task.objects.filter(owner=user, title="Reply to client").count() == 1
    assert mock_extract.call_count == 1  # the LLM was only ever called once