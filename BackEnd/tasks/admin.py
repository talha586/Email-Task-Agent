from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "priority", "due_date", "confidence", "created_at")
    list_filter = ("priority",)
    search_fields = ("title", "description")