from rest_framework import serializers

from chat_app.models import ChatRoom, Message
from users.models import User


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.SerializerMethodField()
    sender_id = serializers.ReadOnlyField(source='sender.id')

    class Meta:
        model = Message
        fields = ['id', 'chat_room', 'sender', 'sender_id', 'sender_username', 'content', 'timestamp', 'is_read','file_type','file']
        read_only_fields = ['id', 'chat_room', 'sender', 'sender_id', 'sender_username', 'timestamp']

    def get_sender_username(self, obj):
        """
        Returns the username of the message sender.
        """
        return obj.sender.username
