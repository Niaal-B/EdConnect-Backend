from django.db import models
from django.conf import settings


class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')

    NOTIFICATION_TYPES = [
        ("connection_request_received", "Connection Request Received"), 
        ("connection_request_accepted", "Connection Request Accepted"), 
    ]

    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    message = models.CharField(max_length=255)

    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=100, null=True, blank=True) 

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'] 

    def __str__(self):
        sender_info = f" from {self.sender.username}" if self.sender else ""
        return f"Notification for {self.recipient.username}: {self.notification_type}{sender_info} ({'Read' if self.is_read else 'Unread'})"