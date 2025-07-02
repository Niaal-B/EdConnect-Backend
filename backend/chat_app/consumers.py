import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.db import models

from chat_app.models import ChatRoom, Message 

User = get_user_model() 


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time chat messages.
    Each instance of this class manages a single, persistent WebSocket connection
    from a client (e.g., a user's browser tab).
    """

    async def connect(self):
        """
        This method is automatically called by Channels when a new WebSocket connection
        is attempted by a client. It's the first point of interaction for a new connection.
        """
        
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"

        if not self.scope["user"].is_authenticated:
            await self.close(code=4001) 
            print(f"WebSocket connection rejected: User not authenticated for room {self.room_name}")
            return

        user = self.scope["user"] 

        try:
            self.chat_room_obj = await sync_to_async(ChatRoom.objects.get)(id=self.room_name)
            student_obj = await sync_to_async(lambda: self.chat_room_obj.student)()
            mentor_obj = await sync_to_async(lambda: self.chat_room_obj.mentor)()

            if not (user == student_obj or user == mentor_obj):
                await self.close(code=4003)
                print(f"WebSocket connection rejected: User {user.username} not authorized for room {self.room_name}")
                return
        except ChatRoom.DoesNotExist:
            await self.close(code=4004) 
            print(f"WebSocket connection rejected: ChatRoom {self.room_name} does not exist.")
            return

        # If all checks pass (authenticated and authorized), formally accept the connection.
        # This completes the WebSocket handshake.
        await self.accept()
        print(f"WebSocket connection accepted for user {user.username} in room {self.room_name}")

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name    
        )

    async def disconnect(self, close_code):
        """
        This method is automatically called by Channels when a WebSocket connection
        is closed (either by the client or the server).
        """
        print(f"WebSocket connection disconnected from room {self.room_name} with code {close_code}")

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name    
        )

    async def receive(self, text_data):
        """
        This method is automatically called by Channels when a message is received
        from the connected WebSocket client.
        """

        text_data_json = json.loads(text_data)
        message_content = text_data_json.get('message')

        if not message_content:
            print("Received empty message content.")
            return
        
        sender = self.scope["user"]

        try:
            new_message = await sync_to_async(Message.objects.create)(
                chat_room=self.chat_room_obj,
                sender=sender,
                content=message_content
            )
            self.chat_room_obj.updated_at = new_message.timestamp
            await sync_to_async(self.chat_room_obj.save)()

            print(f"Message saved: '{message_content}' from {sender.username} in room {self.room_name}")

        except Exception as e:
            print(f"Error saving message to database: {e}")

            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to save message. Please try again.'
            }))
            
            return

        await self.channel_layer.group_send(
            self.room_group_name, 
            {
                'type': 'chat_message', 
                'message': message_content,
                'sender_id': sender.id,
                'sender_username': sender.username,
                'timestamp': new_message.timestamp.isoformat(),
                'chat_room_id': self.room_name
            }
        )

    async def chat_message(self, event):
        message_content = event['message']
        sender_id = event['sender_id']
        sender_username = event['sender_username']
        timestamp = event['timestamp']
        chat_room_id = event['chat_room_id']

        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message_content,
            'sender_id': sender_id,
            'sender_username': sender_username,
            'timestamp': timestamp,
            'chat_room_id': chat_room_id
        }))
        print(f"Message sent to client: '{message_content}' in room {chat_room_id}")