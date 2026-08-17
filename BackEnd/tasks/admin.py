from django.contrib import admin

from .models import Task, ThreadMemory


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "priority", "due_date", "confidence", "created_at")
    list_filter = ("priority",)
    search_fields = ("title", "description")


@admin.register(ThreadMemory)
class ThreadMemoryAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "updated_at")
    search_fields = ("key",)