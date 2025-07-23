from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Connection
from chat_app.models import ChatRoom

@receiver(post_save, sender=Connection)
def create_chat_room_on_accept(sender, instance, created, **kwargs):
    if not created and instance.status == 'accepted':
        ChatRoom.objects.get_or_create(
            student=instance.student,
            mentor=instance.mentor
        )