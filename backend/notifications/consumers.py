import json
from channels.generic.websocket import AsyncWebsocketConsumer
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
        else:
            await self.close()

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

