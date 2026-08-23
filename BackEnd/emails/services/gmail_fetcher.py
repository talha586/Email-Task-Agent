"""Gmail IMAP fetch service.

Credentials come from Django settings (backed by environment variables),
never from a checked-in file. Add to BackEnd/settings.py:

    GMAIL_USER = os.environ["GMAIL_USER"]
    GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
    TASK_SENDER_FILTER = os.environ.get("TASK_SENDER_FILTER", "")

...and put GMAIL_USER / GMAIL_APP_PASSWORD / TASK_SENDER_FILTER in your
.env (which must be gitignored). Rotate any password that was ever
committed in plaintext before reusing it here.
"""

from __future__ import annotations

import email
import imaplib
from typing import Any, Dict, List

from django.conf import settings

from .email_parser import parse_message

DEFAULT_FETCH_LIMIT = 10


def fetch_email_data(
    limit: int = DEFAULT_FETCH_LIMIT, sender_filter: str | None = None
) -> List[Dict[str, Any]]:
    """Log into Gmail via IMAP and return the most recent matching messages.

    Args:
        limit: how many recent matching messages to return.
        sender_filter: if given, searches "FROM" this sender instead of the
            settings.TASK_SENDER_FILTER default. Passing None (the default)
            preserves existing behavior — the settings value, or ALL if
            that's also empty.

    Returns a list of {"message_id", "in_reply_to", "references", "subject",
    "from", "date", "body"} dicts. Returns an empty list (rather than
    raising) on fetch failure, so callers can decide how to surface that to
    the frontend.
    """
    username = getattr(settings, "GMAIL_USER", None)
    password = getattr(settings, "GMAIL_APP_PASSWORD", None)
    effective_sender_filter = sender_filter or (getattr(settings, "TASK_SENDER_FILTER", "") or None)

    if not username or not password:
        raise ValueError("GMAIL_USER / GMAIL_APP_PASSWORD are not configured in settings")

    results: List[Dict[str, Any]] = []

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(username, password)
        mail.select("INBOX")

        if effective_sender_filter:
            typ, data = mail.search(None, "FROM", effective_sender_filter)
        else:
            typ, data = mail.search(None, "ALL")

        if typ != "OK":
            return results

        ids = data[0].split()[-limit:]

        for msg_id in reversed(ids):
            typ, msg_data = mail.fetch(msg_id, "(RFC822)")
            if typ != "OK" or not msg_data:
                continue

            raw = None
            if isinstance(msg_data[0], tuple):
                raw = msg_data[0][1]
            elif isinstance(msg_data[0], bytes):
                raw = msg_data[0]
            if raw is None:
                continue

            msg = email.message_from_bytes(raw)
            results.append(
                {
                    "message_id": msg.get("Message-ID", ""),
                    "in_reply_to": msg.get("In-Reply-To", ""),
                    "references": msg.get("References", ""),
                    "subject": msg.get("Subject", ""),
                    "from": msg.get("From", ""),
                    "date": msg.get("Date", ""),
                    "body": parse_message(msg),
                }
            )

        try:
            mail.close()
        except Exception:
            pass
        mail.logout()

    except Exception as exc:
        # Surface via logging in real usage; kept simple here.
        print(f"IMAP fetch error: {exc}")

    return results