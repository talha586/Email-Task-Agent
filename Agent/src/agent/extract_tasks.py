# """Public Agent API: extract structured tasks from plain email text."""

# from __future__ import annotations

# import os
# from functools import lru_cache
# from pathlib import Path

# from dotenv import load_dotenv

# from .agent_runner import AgentRunner, _parse_tasks_json
# from .model_client import GroqModelClient, ModelClient
# from .schemas import ExtractedTask
# from .tool_registry import ToolRegistry

# ENV_PATH = Path(__file__).resolve().parent.parent.parent / "Config" / ".env"


# def _load_groq_api_key() -> str:
#     if not ENV_PATH.exists():
#         raise FileNotFoundError(f".env (for agent) not found at expected location: {ENV_PATH}")

#     load_dotenv(dotenv_path=str(ENV_PATH))
#     api_key = os.getenv("GROQ_API") or os.getenv("GROQ_API_KEY")
#     if not api_key:
#         raise EnvironmentError(f"GROQ_API (or GROQ_API_KEY) not found in .env at: {ENV_PATH}")
#     return api_key


# def _extract_tasks_tool(*, text: str, model_client: ModelClient) -> list[ExtractedTask]:
#     from .agent_runner import EXTRACTION_SYSTEM_PROMPT

#     response = model_client.complete(text, system=EXTRACTION_SYSTEM_PROMPT)
#     return _parse_tasks_json(response.content)


# @lru_cache(maxsize=1)
# def _build_runner() -> AgentRunner:
#     model_client = GroqModelClient(api_key=_load_groq_api_key())
#     registry = ToolRegistry()
#     registry.register(
#         name="extract_tasks",
#         description="Extract action items from email text as structured JSON tasks.",
#         handler=_extract_tasks_tool,
#     )
#     return AgentRunner(model_client=model_client, tool_registry=registry)


# def extract_tasks(text: str) -> list[ExtractedTask]:
#     """Given cleaned email text, return tasks the recipient needs to perform."""
#     runner = _build_runner()
#     return runner.extract_tasks(text)


"""Agent public API: extract structured tasks from plain email text.

This is the ONLY function Backend should ever call on the Agent package.
The Agent has no knowledge of Gmail, Django, or where the text came from —
it just reasons over text and returns structured tasks.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from .agent_runner import AgentRunner, _parse_tasks_json, EXTRACTION_SYSTEM_PROMPT
from .model_client import GroqModelClient, ModelClient
from .schemas import ExtractedTask
from .tool_registry import ToolRegistry

ENV_PATH = Path(__file__).resolve().parent.parent.parent / "Config" / ".env"


def _load_groq_api_key() -> str:
    if not ENV_PATH.exists():
        raise FileNotFoundError(f".env (for agent) not found at expected location: {ENV_PATH}")

    load_dotenv(dotenv_path=str(ENV_PATH))
    api_key = os.getenv("GROQ_API") or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(f"GROQ_API (or GROQ_API_KEY) not found in .env at: {ENV_PATH}")
    return api_key


def _extract_tasks_tool(*, text: str, model_client: ModelClient) -> list[ExtractedTask]:
    response = model_client.complete(text, system=EXTRACTION_SYSTEM_PROMPT)
    return _parse_tasks_json(response.content)


@lru_cache(maxsize=1)
def _build_runner() -> AgentRunner:
    model_client = GroqModelClient(api_key=_load_groq_api_key())
    registry = ToolRegistry()
    registry.register(
        name="extract_tasks",
        description="Extract action items from email text as structured JSON tasks.",
        handler=_extract_tasks_tool,
    )
    return AgentRunner(model_client=model_client, tool_registry=registry)


def extract_tasks(text: str) -> list[ExtractedTask]:
    """Given cleaned text (e.g. an email body), return the tasks it contains."""
    runner = _build_runner()
    return runner.extract_tasks(text)