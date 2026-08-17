"""A minimal persistent key-value store, backed by the project's database.

This is the Agent's memory layer per the internship proposal: a way for
the pipeline to recognize "have I already handled this email thread?"
across separate scans, so repeated runs don't create duplicate tasks.

The interface is deliberately small (get/set/exists/delete) so the
backing store could later be swapped for Redis or another real KV engine
without changing any calling code in extraction.py.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from BackEnd.tasks.models import ThreadMemory


def get(key: str) -> Optional[Dict[str, Any]]:
    """Return the stored value for ``key``, or None if it doesn't exist."""
    try:
        return ThreadMemory.objects.get(key=key).value
    except ThreadMemory.DoesNotExist:
        return None


def set(key: str, value: Dict[str, Any]) -> None:
    """Store (or overwrite) the value for ``key``."""
    ThreadMemory.objects.update_or_create(key=key, defaults={"value": value})


def exists(key: str) -> bool:
    return ThreadMemory.objects.filter(key=key).exists()


def delete(key: str) -> None:
    ThreadMemory.objects.filter(key=key).delete()