"""Agent public API: extract a person's name from a free-text message.

Same contract style as extract_tasks() in extract_tasks.py — Backend passes
in raw text, gets back a plain Python value, and never has to know
anything about prompts, models, or JSON-parsing details.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache

from .extract_tasks import _load_groq_api_key
from .model_client import GroqModelClient

NAME_EXTRACTION_SYSTEM_PROMPT = """\
You extract a single person's name from a short message, if one is mentioned.
Return ONLY valid JSON — no markdown, no explanation.

Output schema:
{"name": "the person's name" or null}

Examples:
"show me the latest task from sarah" -> {"name": "sarah"}
"what did john ask me to do" -> {"name": "john"}
"show me everything" -> {"name": null}
"""


def _parse_name_json(raw: str) -> str | None:
    """Best-effort parse of the LLM's {"name": ...} JSON output."""
    text = raw.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return None
        try:
            payload = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None

    name = payload.get("name")
    if not name or not isinstance(name, str):
        return None
    return name.strip() or None


@lru_cache(maxsize=1)
def _build_name_model_client() -> GroqModelClient:
    return GroqModelClient(api_key=_load_groq_api_key())


def extract_person_name(message: str) -> str | None:
    """Given a free-text message, return the person's name mentioned in
    it, or None if no name is mentioned.
    """
    if not message or not message.strip():
        return None

    model_client = _build_name_model_client()
    response = model_client.complete(message, system=NAME_EXTRACTION_SYSTEM_PROMPT)
    return _parse_name_json(response.content)