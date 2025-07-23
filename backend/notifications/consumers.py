import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Notification
from .serializers import NotificationSerializer

User = get_user_model()

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"] 

        if self.user.is_authenticated:
            self.notification_group_name = f"user_{self.user.id}_notifications"

            await self.channel_layer.group_add(
                self.notification_group_name,
                self.channel_name
            )
            await self.accept()
            print(f"User {self.user.username} connected to notifications WebSocket.")
        else:
            await self.close()
            print("Unauthenticated user tried to connect to notifications WebSocket.")

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(
                self.notification_group_name,
                self.channel_name
            )
            print(f"User {self.user.username} disconnected from notifications WebSocket.")

    async def receive(self, text_data):
        #For Futre enhancement
        pass

    async def send_notification(self, event):
        notification_data = event['notification_data']

        await self.send(text_data=json.dumps({
            'type': 'notification', 
            'notification': notification_data
        }))
        print(f"Sent real-time notification to {self.user.username}: {notification_data['message']}")

# --- Helper function to create and send notifications ---
@sync_to_async
def create_and_send_notification(recipient_id, sender_id, notification_type, message, related_object_id=None, related_object_type=None):
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

    sync_to_async(channel_layer.group_send)(
        group_name,
        {
            'type': 'send_notification', 
            'notification_data': notification_data
        }
    )
    print(f"Notification created and sent to channel layer for user {recipient.username} (type: {notification_type}).")