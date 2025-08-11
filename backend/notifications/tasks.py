# backend/notifications/tasks.py
import asyncio

from asgiref.sync import sync_to_async
from celery import shared_task
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model

from .models import Notification
from .serializers import NotificationSerializer

User = get_user_model()

@shared_task(bind=True) # `bind=True` allows the task to access itself for retries etc.
def send_realtime_notification_task(self, recipient_id, sender_id, notification_type, message, related_object_id=None, related_object_type=None):
    """
    Celery task to create a Notification in the DB and send it via WebSocket.
    """
    try:
        recipient = User.objects.get(id=recipient_id)
        sender = User.objects.get(id=sender_id) if sender_id else None

        notification = Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            message=message,
            related_object_id=related_object_id,
            related_object_type=related_object_type
        )

        serializer = NotificationSerializer(notification)
        notification_data = serializer.data

        channel_layer = get_channel_layer()
        group_name = f"user_{recipient.id}_notifications"

        asyncio.run(
            channel_layer.group_send(
                group_name,
                {
                    'type': 'send_notification',
                    'notification_data': notification_data
                }
            )
        )

    except Exception as exc:
        self.retry(exc=exc, countdown=60, max_retries=5)
