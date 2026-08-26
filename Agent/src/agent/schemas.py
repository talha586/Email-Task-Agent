"""Structured output schemas for extracted tasks."""

from __future__ import annotations

from typing import TypedDict


class ExtractedTask(TypedDict, total=False):
    title: str
    description: str
    due_date: str | None
    priority: str | None
    confidence: float
