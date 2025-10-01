from asgiref.sync import sync_to_async
from auth.authentication import CookieJWTAuthentication
from chat_app.models import ChatRoom
from connections.models import Connection
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from notifications.tasks import send_realtime_notification_task
from rest_framework import generics, permissions, status
from rest_framework.exceptions import (NotFound, PermissionDenied,
                                       ValidationError)
from rest_framework.response import Response
from rest_framework.views import APIView
from users.models import User

from .serializers import (ConnectionRequestSerializer, ConnectionSerializer,
                          ConnectionStatusUpdateSerializer,
                          ConnectionWithStudentSerializer,
                          MentorConnectionSerializer,
                          StudentConnectionSerializer)


class RequestConnectionView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=ConnectionRequestSerializer,
        responses={201: ConnectionSerializer, 400: dict, 403: dict}
    )
    def post(self, request):
        serializer = ConnectionRequestSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        student = request.user
        mentor = serializer.validated_data['mentor']

        connection, created = Connection.objects.get_or_create(
            student=student,
            mentor=mentor,
            defaults={"status": "pending"}
        )

        if not created:
            if connection.status == "accepted":
                raise ValidationError("You are already connected with this mentor.")
            else:
                connection.status = "pending"
                connection.save(update_fields=["status", "updated_at"])

        send_realtime_notification_task.delay(
            recipient_id=mentor.id,
            sender_id=student.id,
            notification_type='connection_request_received',
            message=f"{student.username} has sent you a connection request.",
            related_object_id=connection.id,
            related_object_type='Connection'
        )

        return Response(ConnectionSerializer(connection).data, status=status.HTTP_201_CREATED)
class PendingRequestsView(generics.ListAPIView):
    serializer_class = ConnectionWithStudentSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Connection.objects.filter(mentor=self.request.user, status='pending')


class ManageConnectionStatus(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        user = request.user

        if user.role != 'mentor':
            return Response({'detail': 'Only mentors can update connection status.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            connection = Connection.objects.get(pk=pk, mentor=user)
        except Connection.DoesNotExist:
            return Response({'detail': 'Connection not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ConnectionStatusUpdateSerializer(connection, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        old_status = connection.status
        connection = serializer.save()

        if connection.status == 'accepted' and old_status != 'accepted':
            send_realtime_notification_task.delay(
                recipient_id=connection.student.id,
                sender_id=user.id,
                notification_type='connection_request_accepted',
                message=f"{user.username} has accepted your connection request!.",
                related_object_id=connection.id,
                related_object_type='Connection'
            )

        return Response(ConnectionSerializer(connection).data, status=status.HTTP_200_OK)



class ListConnectionsView(generics.ListAPIView):
    serializer_class = ConnectionSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'student':
            return Connection.objects.filter(student=user)
        elif user.role == 'mentor':
            return Connection.objects.filter(mentor=user)
        return Connection.objects.none()


class CancelConnectionView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        try:
            connection = Connection.objects.get(pk=pk, student=request.user)
        except Connection.DoesNotExist:
            return Response({'detail': 'Connection not found or not owned by you.'}, status=status.HTTP_404_NOT_FOUND)

        if connection.status != 'pending':
            return Response({'detail': 'Only pending requests can be cancelled.'}, status=status.HTTP_400_BAD_REQUEST)

        connection.delete()

        send_realtime_notification_task.delay(
            recipient_id=connection.mentor.id,
            sender_id=request.user.id,
            notification_type='connection_request_cancelled',
            message=f"{request.user.username} cancelled their connection request.",
            related_object_id=connection.id,
            related_object_type='Connection'
        )

        return Response({'detail': 'Connection request cancelled successfully.'}, status=status.HTTP_204_NO_CONTENT)


class MyMentorsView(generics.ListAPIView):
    serializer_class = MentorConnectionSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Connection.objects
            .filter(student=user, status='accepted')
            .select_related('mentor', 'mentor__mentor_profile')
            .prefetch_related('mentor__slots')  
        )

class MyStudentsView(generics.ListAPIView):
    serializer_class = StudentConnectionSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            Connection.objects
            .filter(mentor=user, status='accepted')
            .select_related('student', 'student__student_profile'))