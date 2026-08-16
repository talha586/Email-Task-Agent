"""Orchestrates the email -> task pipeline.

This is the only place that talks to both the emails app and the Agent
package — it fetches, cleans (already done by the emails service), calls
the Agent for extraction, and aggregates results for the API layer.
"""

from __future__ import annotations

from typing import Any, Dict, List

from agent import extract_tasks  # Agent's sole public entry point

from BackEnd.emails.services import fetch_email_data


def run_extraction(limit: int = 10) -> Dict[str, Any]:
    """Fetch recent emails and extract tasks from each.

    Returns:
        {
          "messages_fetched": int,
          "results": [
              {"subject": str, "from": str, "date": str, "tasks": [...]},
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
        email_text = f"Subject: {subject}\n\n{body}"

        try:
            tasks = extract_tasks(email_text)
        except Exception as exc:
            tasks = []
            print(f"Task extraction failed for '{subject}': {exc}")

        results.append(
            {
                "subject": subject,
                "from": message.get("from", ""),
                "date": message.get("date", ""),
                "tasks": tasks,
            }
        )
        total_tasks += len(tasks)

    return {
        "messages_fetched": len(messages),
        "results": results,
        "total_tasks": total_tasks,
    }