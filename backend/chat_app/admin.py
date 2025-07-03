# backend/chat_app/admin.py

from django.contrib import admin
from .models import ChatRoom, Message

# Register your models here.

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    """
    Admin configuration for the ChatRoom model.
    """
    list_display = ('id', 'student', 'mentor', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('student__username', 'mentor__username')
    raw_id_fields = ('student', 'mentor') # Use raw_id_fields for ForeignKey to User for better UX with many users

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Message model.
    """
    list_display = ('id', 'chat_room', 'sender', 'timestamp', 'is_read', 'content_preview')
    list_filter = ('timestamp', 'is_read', 'chat_room')
    search_fields = ('content', 'sender__username', 'chat_room__student__username', 'chat_room__mentor__username')
    raw_id_fields = ('chat_room', 'sender') # Use raw_id_fields for ForeignKey for better UX

    def content_preview(self, obj):
        """
        Displays a truncated preview of the message content in the list view.
        """
        return obj.content[:75] + '...' if len(obj.content) > 75 else obj.content
    content_preview.short_description = 'Content' # Column header for the preview
