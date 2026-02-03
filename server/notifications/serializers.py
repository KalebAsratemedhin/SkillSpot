from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source='actor.email', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'recipient',
            'title',
            'message',
            'link',
            'actor',
            'actor_email',
            'read',
            'read_at',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'recipient',
            'title',
            'message',
            'link',
            'actor',
            'created_at',
        ]


class NotificationMarkReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['read']




