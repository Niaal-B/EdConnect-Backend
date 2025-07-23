# backend/notifications/serializers.py
from rest_framework import serializers
from .models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

class NotificationSerializer(serializers.ModelSerializer):
    sender_username = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id', 
            'recipient', 
            'sender', 
            'sender_username', 
            'notification_type', 
            'message', 
            'related_object_id', 
            'related_object_type', 
            'is_read', 
            'created_at'
        ]
        read_only_fields = [
            'id', 
            'recipient', 
            'sender', 
            'sender_username', 
            'created_at'
        ]

    def get_sender_username(self, obj):
        """
        Returns the username of the sender, or a default if no sender.
        """
        return obj.sender.username if obj.sender else "System" 