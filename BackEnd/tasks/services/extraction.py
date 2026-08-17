"""Orchestrates the email -> task pipeline, persisting to the DB and using
the KV-store memory layer (see services/kv_store.py) to avoid re-extracting
tasks from emails belonging to a thread that's already been processed.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from agent import extract_tasks  # Agent's sole public entry point

from BackEnd.emails.models import FetchedEmail
from BackEnd.emails.services import fetch_email_data
from BackEnd.tasks.models import Task
from BackEnd.tasks.services import kv_store

_RE_SUBJECT_PREFIX = re.compile(r"^(re|fwd?):\s*", re.IGNORECASE)


def _thread_key(message: Dict[str, Any]) -> str:
    """Best-effort identifier for the email thread this message belongs to.

    Prefers the thread's root message id from References (the first entry
    is the original message per RFC 5322), then In-Reply-To, then falls
    back to this message's own Message-ID, then a normalized subject as a
    last resort for mail clients that omit threading headers entirely.
    """
    references = (message.get("references") or "").split()
    if references:
        return references[0].strip()

    in_reply_to = (message.get("in_reply_to") or "").strip()
    if in_reply_to:
        return in_reply_to

    message_id = (message.get("message_id") or "").strip()
    if message_id:
        return message_id

    subject = (message.get("subject") or "").strip().lower()
    return _RE_SUBJECT_PREFIX.sub("", subject)


def _parse_due_date(value: Any) -> Optional[date]:
    """Best-effort parse of the Agent's 'YYYY-MM-DD' due_date string."""
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def run_extraction(limit: int = 10) -> Dict[str, Any]:
    """Fetch recent emails, extract tasks from each (skipping known
    threads via the KV memory), and save everything to the DB.

    Returns:
        {
          "messages_fetched": int,
          "results": [
              {"email_id": int, "subject": str, "from": str, "date": str,
               "thread_key": str, "from_memory": bool,
               "tasks": [{"id": int, "title": str, ...}, ...]},
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
        thread_key = _thread_key(message)

        email_record = FetchedEmail.objects.create(
            message_id=message.get("message_id") or None,
            in_reply_to=message.get("in_reply_to") or None,
            references=message.get("references") or None,
            subject=subject,
            sender=message.get("from", ""),
            date=message.get("date", ""),
            body=body,
        )

        memory_entry = kv_store.get(thread_key)

        if memory_entry is not None:
            # Already processed this thread on a previous scan — reuse the
            # tasks we already created instead of asking the LLM again.
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
                for t in Task.objects.filter(id__in=known_task_ids)
            ]
            results.append(
                {
                    "email_id": email_record.id,
                    "subject": subject,
                    "from": message.get("from", ""),
                    "date": message.get("date", ""),
                    "thread_key": thread_key,
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
            thread_key,
            {
                "task_ids": [t["id"] for t in saved_tasks],
                "last_message_id": message.get("message_id", ""),
            },
        )

        results.append(
            {
                "email_id": email_record.id,
                "subject": subject,
                "from": message.get("from", ""),
                "date": message.get("date", ""),
                "thread_key": thread_key,
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