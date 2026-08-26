from django.contrib import admin

from .models import FetchedEmail


@admin.register(FetchedEmail)
class FetchedEmailAdmin(admin.ModelAdmin):
    list_display = ("subject", "sender", "date", "fetched_at")
    search_fields = ("subject", "sender", "body")