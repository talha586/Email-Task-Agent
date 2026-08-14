"""Agent runner: orchestrates model calls and tool usage for task extraction."""

from __future__ import annotations          #-> Helps in type hinting

import json
import re
from typing import Any

from .model_client import ModelClient
from .schemas import ExtractedTask
from .tool_registry import ToolRegistry

EXTRACTION_SYSTEM_PROMPT = """\
You are an email task extraction assistant. Given email text, identify concrete action items \
the recipient must do. Return ONLY valid JSON — no markdown, no explanation.

Output schema:
{
  "tasks": [
    {
      "title": "short action title",
      "description": "what needs to be done",
      "due_date": "YYYY-MM-DD or null if unknown",
      "priority": "low|medium|high or null",
      "confidence": 0.0 to 1.0
    }
  ]
}

If there are no action items, return {"tasks": []}.
"""


def _parse_tasks_json(raw: str) -> list[ExtractedTask]:
    """Best-effort parse of LLM JSON output."""
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
            return []
        payload = json.loads(text[start : end + 1])

    tasks = payload.get("tasks", [])
    if not isinstance(tasks, list):
        return []

    normalized: list[ExtractedTask] = []
    for item in tasks:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        if not title:
            continue
        normalized.append(
            ExtractedTask(
                title=title,
                description=str(item.get("description", "")).strip(),
                due_date=item.get("due_date"),
                priority=item.get("priority"),
                # confidence=float(item.get("confidence", 0.5)),
            )
        )
    return normalized


class AgentRunner:
    """Runs the extract-tasks pipeline using a model client and optional tools."""

    def __init__(self, model_client: ModelClient, tool_registry: ToolRegistry | None = None) -> None:
        self._model = model_client
        self._tools = tool_registry or ToolRegistry()

    @property
    def tools(self) -> ToolRegistry:
        return self._tools

    def extract_tasks(self, text: str) -> list[ExtractedTask]:
        """Extract action items from email text via the registered model client."""
        if not text or not text.strip():
            return []

        extract_tool = self._tools.get("extract_tasks")
        if extract_tool is not None:
            return extract_tool.handler(text=text, model_client=self._model)

        response = self._model.complete(text, system=EXTRACTION_SYSTEM_PROMPT)
        return _parse_tasks_json(response.content)

    def run_tool(self, name: str, **kwargs: Any) -> Any:
        return self._tools.run(name, **kwargs)
