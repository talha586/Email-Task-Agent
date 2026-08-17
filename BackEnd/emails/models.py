from django.db import models


class FetchedEmail(models.Model):
    """A single email pulled from the inbox by gmail_fetcher.py."""

    message_id = models.CharField(max_length=255, blank=True, null=True)
    subject = models.CharField(max_length=500, blank=True)
    sender = models.CharField(max_length=255, blank=True)
    date = models.CharField(max_length=255, blank=True)  # raw Date header as fetched
    body = models.TextField(blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fetched_at"]

    def __str__(self) -> str:
        return self.subject or f"Email #{self.pk}"