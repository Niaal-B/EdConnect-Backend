from django.db import models
from django.conf import settings

class ChatRoom(models.Model):
    """
    Represents a one-to-one chat room between a student and a mentor.
    Ensures that there's only one chat room per student-mentor pair.
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_chat_rooms',
        help_text="The student participating in this chat room."
    )

    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mentor_chat_rooms', 
        help_text="The mentor participating in this chat room."
    )

    created_at = models.DateTimeField(auto_now_add=True,)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Meta options for the ChatRoom model.
        """
        # Ensures that a unique chat room exists for each student-mentor pair.
        # The combination of student and mentor must be unique.
        unique_together = ('student', 'mentor') 
        verbose_name = "Chat Room"
        verbose_name_plural = "Chat Rooms"
        ordering = ['-updated_at'] 

    def __str__(self):
        """
        String representation of the ChatRoom object.
        """
        return f"Chat between {self.student.username} and {self.mentor.username}"


class Message(models.Model):
    """
    Represents a single message within a chat room.
    """
    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE, 
        related_name='messages'
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages', 
        help_text="The user who sent this message."
    )
    
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    file = models.FileField(upload_to='chat_media/', blank=True, null=True)
    file_type = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        """
        Meta options for the Message model.
        """
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ['timestamp']

    def __str__(self):
        """
        String representation of the Message object.
        """
        return f"Message from {self.sender.username} in {self.chat_room} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}: {self.content[:50]}..."
