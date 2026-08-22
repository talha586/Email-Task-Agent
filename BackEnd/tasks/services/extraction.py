"""Orchestrates the email -> task pipeline.

Every Task created here is owned by the authenticated user who triggered
the scan — ownership always comes from ``user`` (request.user upstream),
never from anything client-supplied.

The KV memory layer is keyed per (user, message) rather than per thread:
keying by thread would mean a brand-new reply gets thrown away just
because an earlier message in the same thread was already processed.
Keying by user+message also means one user's scan can never reuse or
expose tasks that belong to another user.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from agent import extract_tasks  # Agent's sole public entry point

from BackEnd.emails.models import FetchedEmail
from BackEnd.emails.services import fetch_email_data
from BackEnd.tasks.models import Task
from BackEnd.tasks.services import kv_store


def _memory_key(user_id: int, message: Dict[str, Any]) -> str:
    """Per-user, per-message memory key.

    Deliberately NOT the thread root — that was the bug: keying by thread
    meant one processed message marked the whole thread as done, so a
    genuinely new reply in that thread was skipped and its tasks were
    never created.
    """
    message_id = (message.get("message_id") or "").strip()
    if message_id:
        return f"{user_id}:{message_id}"

    # Rare fallback for mail with no Message-ID header at all — still
    # scoped to this user, just less precise than a real message id.
    subject = (message.get("subject") or "").strip().lower()
    date_hdr = (message.get("date") or "").strip()
    return f"{user_id}:{subject}|{date_hdr}"


def _parse_due_date(value: Any) -> Optional[date]:
    """Best-effort parse of the Agent's 'YYYY-MM-DD' due_date string."""
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def run_extraction(user, limit: int = 10) -> Dict[str, Any]:
    """Fetch recent emails and extract tasks from each new message.

    Args:
        user: the authenticated Django user making this request. Every
            Task row created is owned by this user; never pass anything
            derived from client input here.
        limit: how many recent emails to check.

    Returns:
        {
          "messages_fetched": int,
          "results": [
              {"email_id": int, "subject": str, "from": str, "date": str,
               "from_memory": bool, "tasks": [{"id": int, ...}, ...]},
              ...
          ],
          "total_tasks": int,
        }
    """
    messages = fetch_email_data(limit=limit)

    results: List[Dict[str, Any]] = []
    total_tasks = 0

    for message in messages:
        subject = message.get("subject", "(no subject)")
        body = message.get("body", "")
        memory_key = _memory_key(user.id, message)

        email_record = FetchedEmail.objects.create(
            message_id=message.get("message_id") or None,
            in_reply_to=message.get("in_reply_to") or None,
            references=message.get("references") or None,
            subject=subject,
            sender=message.get("from", ""),
            date=message.get("date", ""),
            body=body,
        )

        memory_entry = kv_store.get(memory_key)

        if memory_entry is not None:
            # This exact message, for this exact user, was already
            # processed on a previous scan — reuse its tasks rather than
            # asking the LLM again. A *different* message in the same
            # thread, or the same message for a different user, will
            # have a different key and will NOT hit this branch.
            known_task_ids = memory_entry.get("task_ids", [])
            saved_tasks = [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "due_date": t.due_date,
                    "priority": t.priority,
                    "confidence": t.confidence,
                }
                for t in Task.objects.filter(id__in=known_task_ids, owner=user)
            ]
            results.append(
                {
                    "email_id": email_record.id,
                    "subject": subject,
                    "from": message.get("from", ""),
                    "date": message.get("date", ""),
                    "from_memory": True,
                    "tasks": saved_tasks,
                }
            )
            total_tasks += len(saved_tasks)
            continue

        email_text = f"Subject: {subject}\n\n{body}"
        try:
            tasks = extract_tasks(email_text)
        except Exception as exc:
            tasks = []
            print(f"Task extraction failed for '{subject}': {exc}")

        saved_tasks: List[Dict[str, Any]] = []
        for task in tasks:
            task_obj = Task.objects.create(
                owner=user,
                title=str(task.get("title", ""))[:255],
                description=task.get("description", "") or "",
                due_date=_parse_due_date(task.get("due_date")),
                priority=task.get("priority") or None,
                confidence=task.get("confidence"),
            )
            saved_tasks.append(
                {
                    "id": task_obj.id,
                    "title": task_obj.title,
                    "description": task_obj.description,
                    "due_date": task_obj.due_date,
                    "priority": task_obj.priority,
                    "confidence": task_obj.confidence,
                }
            )

        kv_store.set(
            memory_key,
            {
                "task_ids": [t["id"] for t in saved_tasks],
                "message_id": message.get("message_id", ""),
            },
        )

        results.append(
            {
                "email_id": email_record.id,
                "subject": subject,
                "from": message.get("from", ""),
                "date": message.get("date", ""),
                "from_memory": False,
                "tasks": saved_tasks,
            }
        )
        total_tasks += len(saved_tasks)

    return {
        "messages_fetched": len(messages),
        "results": results,
        "total_tasks": total_tasks,
    }