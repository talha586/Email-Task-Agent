from django.conf import settings
from django.db import models


class Task(models.Model):
    """A single action item extracted from an email by the Agent."""

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    # Set ONLY from request.user in the view/service layer — never from
    # client-supplied data. null=True because rows created before this
    # field existed have no owner; every new row always sets it.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=Priority.choices, null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    # Raw "From" header of the source email, copied at creation time so
    # "find the latest task from X" can be a plain DB filter — no FK to
    # FetchedEmail, just a denormalized string.
    sender = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class ThreadMemory(models.Model):
    """Generic persistent key-value store — the Agent's memory layer.

    ``key`` is per (user, message) — see extraction.py's ``_memory_key`` —
    deliberately NOT per email thread. A thread-level key would mean a
    brand-new reply gets skipped just because some earlier message in the
    same thread was already processed; keying per message means every
    individual email is still evaluated on its own.
    """

    key = models.CharField(max_length=255, unique=True)
    value = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.key