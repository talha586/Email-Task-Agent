from rest_framework import serializers

from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    # Read-only: shown for transparency, but a client can never set or
    # change who owns a task through this serializer.
    owner = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        model = Task
        fields = ["id", "owner", "title", "description", "due_date", "priority", "confidence", "created_at"]
        read_only_fields = ["id", "owner", "created_at"]