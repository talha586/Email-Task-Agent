from django.db import models  # noqa: F401

# No models yet — fetched emails are currently handled in-memory per request
# via services/gmail_fetcher.py. Add a model here if you want to persist
# fetched emails (e.g. for thread-dedupe in a later phase).