"""Given a free-text message, extract a person's name via the Agent, then
find the most recent task from that person.

Two-step design, DB-first with a live fallback:
  1. Extracting a name from an arbitrary sentence is genuinely ambiguous —
     worth an LLM call.
  2. Once we have a name, first check what's already in the database (an
     instant, unambiguous filter — no reason to involve the LLM or Gmail
     for this part). Most searches hit this and return immediately.
  3. Only on a miss — nothing on file yet for that name — do a live,
     sender-scoped Gmail fetch via the same run_extraction() pipeline the
     regular "Scan Inbox" button uses, so a search for someone who just
     emailed still finds their task instead of coming back empty because
     no one has re-scanned since.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from agent import extract_person_name

from BackEnd.tasks.models import Task
from BackEnd.tasks.services.extraction import run_extraction


def _serialize_task(task: Task) -> Dict[str, Any]:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "due_date": task.due_date,
        "priority": task.priority,
        "confidence": task.confidence,
        "sender": task.sender,
        "created_at": task.created_at,
    }


def _latest_task_from_db(user, name: str) -> Optional[Task]:
    return (
        Task.objects.filter(owner=user, sender__icontains=name)
        .order_by("-created_at")
        .first()
    )


def find_latest_task_by_name(user, message: str) -> Dict[str, Any]:
    """Returns:
        {"name": str | None, "task": {...} | None, "message": str}

    Always scoped to ``user`` — never trusts anything else for whose
    tasks/inbox to search.
    """
    try:
        name = extract_person_name(message)
    except Exception as exc:
        print(f"Name extraction failed: {exc}")
        return {
            "name": None,
            "task": None,
            "message": "Sorry, I couldn't process that message right now. Please try again.",
        }

    if not name:
        return {
            "name": None,
            "task": None,
            "message": "I couldn't find a person's name in that message.",
        }

    # Fast path: already have something on file for this person.
    task = _latest_task_from_db(user, name)
    if task is not None:
        return {
            "name": name,
            "task": _serialize_task(task),
            "message": f"Latest task from {name}.",
        }

    # Fallback: nothing on file yet — check the actual inbox live, scoped
    # to just this sender. Reuses the same pipeline as a normal scan, so
    # memory-dedupe and owner-scoping both apply exactly as they always do.
    run_extraction(user=user, limit=1, sender_filter=name)

    task = _latest_task_from_db(user, name)
    if task is None:
        return {
            "name": name,
            "task": None,
            "message": f"No tasks found from anyone matching '{name}'.",
        }

    return {
        "name": name,
        "task": _serialize_task(task),
        "message": f"Latest task from {name}.",
    }