from django.db import models


class Task(models.Model):
    """A single action item extracted from an email by the Agent."""

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=Priority.choices, null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class ThreadMemory(models.Model):
    """Generic persistent key-value store — the Agent's memory layer.

    Not tied to Task/FetchedEmail via FK on purpose (keeps it a genuine
    KV store rather than a relational join table). ``key`` is normally an
    email thread's root identifier (see extraction.py's ``_thread_key``);
    ``value`` is a small JSON blob describing what's already been done for
    that key, e.g. {"task_ids": [1, 2], "last_message_id": "<...>"}.
    """

    key = models.CharField(max_length=255, unique=True)
    value = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.key