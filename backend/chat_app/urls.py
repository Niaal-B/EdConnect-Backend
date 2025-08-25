from django.urls import path

from .views import ChatRoomMessageListView

urlpatterns = [
    path('rooms/<int:room_id>/messages/', ChatRoomMessageListView.as_view(), name='chat-room-messages'),
]
