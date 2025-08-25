from auth.authentication import CookieJWTAuthentication
from chat_app.models import ChatRoom, Message
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema  # <<< ADD THIS IMPORT
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .serializers import MessageSerializer


class ChatRoomMessageListView(generics.ListAPIView):
    """
    API endpoint to list all messages for a specific chat room.
    Requires authentication and ensures the requesting user is a participant
    in the specified chat room.
    """
    serializer_class = MessageSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'room_id', # The name of your URL path parameter
                openapi.IN_PATH, # It's a path parameter
                description="ID of the chat room (integer).",
                type=openapi.TYPE_INTEGER, # <<< Explicitly set type to INTEGER
                required=True,
            ),
        ]
    )
    def get_queryset(self):
        chat_room_id = self.kwargs['room_id']
        current_user = self.request.user
        chat_room = get_object_or_404(ChatRoom, id=chat_room_id)

        if not (current_user == chat_room.student or current_user == chat_room.mentor):
            self.permission_denied(
                self.request,
                message="You are not authorized to view messages in this chat room."
            )

        return Message.objects.filter(chat_room=chat_room).order_by('timestamp')
