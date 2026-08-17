# """Orchestrates the email -> task pipeline.

# This is the only place that talks to both the emails app and the Agent
# package — it fetches, cleans (already done by the emails service), calls
# the Agent for extraction, and aggregates results for the API layer.
# """

# from __future__ import annotations

# from typing import Any, Dict, List

# from agent import extract_tasks  # Agent's sole public entry point

# from BackEnd.emails.services import fetch_email_data


# def run_extraction(limit: int = 10) -> Dict[str, Any]:
#     """Fetch recent emails and extract tasks from each.

#     Returns:
#         {
#           "messages_fetched": int,
#           "results": [
#               {"subject": str, "from": str, "date": str, "tasks": [...]},
#               ...
#           ],
#           "total_tasks": int,
#         }
#     """
#     messages = fetch_email_data(limit=limit)

#     results: List[Dict[str, Any]] = []
#     total_tasks = 0

#     for message in messages:
#         subject = message.get("subject", "(no subject)")
#         body = message.get("body", "")
#         email_text = f"Subject: {subject}\n\n{body}"

#         try:
#             tasks = extract_tasks(email_text)
#         except Exception as exc:
#             tasks = []
#             print(f"Task extraction failed for '{subject}': {exc}")

#         results.append(
#             {
#                 "subject": subject,
#                 "from": message.get("from", ""),
#                 "date": message.get("date", ""),
#                 "tasks": tasks,
#             }
#         )
#         total_tasks += len(tasks)

#     return {
#         "messages_fetched": len(messages),
#         "results": results,
#         "total_tasks": total_tasks,
#     }

"""Orchestrates the email -> task pipeline, persisting both sides to the DB.

This is the only place that talks to both the emails app and the Agent
package — it fetches, cleans, calls the Agent for extraction, saves the
results, and aggregates a response for the API layer.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from agent import extract_tasks  # Agent's sole public entry point

from BackEnd.emails.models import FetchedEmail
from BackEnd.emails.services import fetch_email_data
from BackEnd.tasks.models import Task


def _parse_due_date(value: Any) -> Optional[date]:
    """Best-effort parse of the Agent's 'YYYY-MM-DD' due_date string."""
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def run_extraction(limit: int = 10) -> Dict[str, Any]:
    """Fetch recent emails, extract tasks from each, and save both to the DB."""
    messages = fetch_email_data(limit=limit)

    results: List[Dict[str, Any]] = []
    total_tasks = 0

    for message in messages:
        subject = message.get("subject", "(no subject)")
        body = message.get("body", "")
        email_text = f"Subject: {subject}\n\n{body}"

        email_record = FetchedEmail.objects.create(
            message_id=message.get("message_id") or None,
            subject=subject,
            sender=message.get("from", ""),
            date=message.get("date", ""),
            body=body,
        )

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

        results.append(
            {
                "email_id": email_record.id,
                "subject": subject,
                "from": message.get("from", ""),
                "date": message.get("date", ""),
                "tasks": saved_tasks,
            }
        )
        total_tasks += len(saved_tasks)

    return {
        "messages_fetched": len(messages),
        "results": results,
        "total_tasks": total_tasks,
    }