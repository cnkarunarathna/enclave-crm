from rest_framework import serializers

from apps.organizations.models import User

from .models import ActivityLog


class ActivityUserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "full_name"]


class ActivityLogSerializer(serializers.ModelSerializer):
    # null when the acting user was removed; user_email still tells who it was.
    user = ActivityUserSerializer(read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            "id",
            "user",
            "user_email",
            "action",
            "model_name",
            "object_id",
            "object_repr",
            "changes",
            "timestamp",
        ]
        read_only_fields = fields
