"""Pure text-extraction helpers for raw email messages.

No network/IMAP calls live here on purpose — this module only turns an
``email.message.Message`` into plain text, so it can be unit-tested without
a mailbox.
"""

from __future__ import annotations

import html as html_module
import re
from email.message import Message
from typing import List

from bs4 import BeautifulSoup


def html_to_text(html: str) -> str:
    """Convert an HTML email body to plain text."""
    try:
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ")
        text = html_module.unescape(text)
        return re.sub(r"\s+", " ", text).strip()
    except Exception:
        return ""


def parse_message(msg: Message) -> str:
    """Extract a best-effort plain-text body from an email.message.Message.

    Prefers text/plain parts; falls back to text/html (converted to text).
    """
    if msg.is_multipart():
        plain_chunks: List[str] = []
        html_chunks: List[str] = []

        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type not in ("text/plain", "text/html"):
                continue

            payload = part.get_payload(decode=True)
            if payload is None:
                continue

            charset = part.get_content_charset() or "utf-8"
            try:
                decoded = payload.decode(charset, errors="replace")
            except Exception:
                decoded = payload.decode("utf-8", errors="replace")

            (plain_chunks if content_type == "text/plain" else html_chunks).append(decoded)

        if plain_chunks:
            return "\n\n".join(plain_chunks).strip()
        if html_chunks:
            return html_to_text("\n\n".join(html_chunks))
        return ""

    payload = msg.get_payload(decode=True)
    if payload is None:
        payload = msg.get_payload()
        return payload if isinstance(payload, str) else ""

    charset = msg.get_content_charset() or "utf-8"
    try:
        text = payload.decode(charset, errors="replace")
    except Exception:
        text = payload.decode("utf-8", errors="replace")

    if msg.get_content_type() == "text/html":
        return html_to_text(text)
    return text