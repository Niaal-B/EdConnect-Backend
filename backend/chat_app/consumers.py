import base64
import json
import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from chat_app.models import ChatRoom, Message
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from notifications.tasks import send_realtime_notification_task


User = get_user_model() 
logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time chat messages.
    """

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"
        user = self.scope["user"]

        if not user.is_authenticated:
            logger.warning(f"WebSocket connection rejected: User not authenticated for room {self.room_name}")
            await self.close(code=4001) 
            return

        try:
            self.chat_room_obj = await sync_to_async(ChatRoom.objects.get)(id=self.room_name)
            student_obj = await sync_to_async(lambda: self.chat_room_obj.student)()
            mentor_obj = await sync_to_async(lambda: self.chat_room_obj.mentor)()

            if not (user == student_obj or user == mentor_obj):
                logger.warning(f"WebSocket connection rejected: User {user.username} not authorized for room {self.room_name}")
                await self.close(code=4003)
                return
        except ChatRoom.DoesNotExist:
            logger.error(f"WebSocket connection rejected: ChatRoom {self.room_name} does not exist.")
            await self.close(code=4004) 
            return

        await self.accept()
        logger.info(f"WebSocket connection accepted for user {user.username} in room {self.room_name}")

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name    
        )

    async def disconnect(self, close_code):
        logger.info(f"WebSocket connection disconnected from room {self.room_name} with code {close_code}")

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name    
        )
    
    @sync_to_async
    def save_message_with_media(self, chat_room_obj, sender, content=None, file_data=None, file_name=None, file_type=None):
        """Helper function to save message with or without media."""
        new_message = Message(
            chat_room=chat_room_obj,
            sender=sender,
            content=content
        )
        
        if file_data and file_name and file_type:
            try:
                # Split the Base64 string to get just the data
                format, imgstr = file_data.split(';base64,')
                data = ContentFile(base64.b64decode(imgstr), name=file_name)
                new_message.file = data
                new_message.file_type = file_type
                logger.info(f"Successfully decoded and attached file {file_name}")
            except Exception as e:
                logger.error(f"Error decoding Base64 file data: {e}")

        new_message.save()
        return new_message

    async def receive(self, text_data):
        logger.info(text_data)
        text_data_json = json.loads(text_data)
        message_content = text_data_json.get('message')
        file_data = text_data_json.get('file_data')
        file_name = text_data_json.get('file_name')
        file_type = text_data_json.get('file_type')
        
        if not message_content and not file_data:
            logger.warning("Received empty message and no file.")
            return

        sender = self.scope["user"]

        try:
            # Pass all the necessary data to the saving function
            new_message = await self.save_message_with_media(
                self.chat_room_obj, 
                sender, 
                message_content, 
                file_data, 
                file_name, 
                file_type
            )
            
            self.chat_room_obj.updated_at = new_message.timestamp
            await sync_to_async(self.chat_room_obj.save)()
            
            logger.info(f"Message saved from {sender.username} in room {self.room_name}")

        except Exception as e:
            logger.error(f"Error saving message to database: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to save message. Please try again.'
            }))
            return

        recipient = (
            self.chat_room_obj.mentor 
            if sender == self.chat_room_obj.student 
            else self.chat_room_obj.student
        )

        await sync_to_async(send_realtime_notification_task.delay)(
        recipient_id=recipient.id,
        sender_id=sender.id,
        notification_type='message_received',
        message=f"{sender.username} sent you a message.",
        related_object_id=self.chat_room_obj.id,
        related_object_type='ChatRoom'
    )

        response = {
            'type': 'chat_message', 
            'message': new_message.content, 
            'sender_id': sender.id,
            'sender_username': sender.username,
            'timestamp': new_message.timestamp.isoformat(),
            'chat_room_id': self.room_name,
        }

        if new_message.file:
            response['file_url'] = new_message.file.url
            response['file_type'] = new_message.file_type
        
        await self.channel_layer.group_send(
            self.room_group_name, 
            response
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))
        logger.info(f"Message sent to client in room {event.get('chat_room_id')}")