from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from connections.models import Connection
from .serializers import ConnectionSerializer,ConnectionRequestSerializer,ConnectionWithStudentSerializer,MentorConnectionSerializer,StudentConnectionSerializer
from auth.authentication import CookieJWTAuthentication
from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404
from users.models import User
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from chat_app.models import ChatRoom
from asgiref.sync import sync_to_async 
from notifications.tasks import send_realtime_notification_task 
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied




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

        connection = Connection.objects.create(student=student, mentor=mentor)

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
            return Response({'detail': 'Only mentors can update connection status.'}, status=403)

        try:
            connection = Connection.objects.get(pk=pk, mentor=user)
        except Connection.DoesNotExist:
            return Response({'detail': 'Connection not found.'}, status=404)

        status_choice = request.data.get('status')
        if status_choice not in ['accepted', 'rejected']:
            return Response({'detail': 'Invalid status.'}, status=400)

        old_status = connection.status
        connection.status = status_choice
        connection.save()

        if status_choice == 'accepted' and old_status != 'accepted':
            send_realtime_notification_task.delay(
                recipient_id=connection.student.id,
                sender_id=user.id,
                notification_type='connection_request_accepted',
                message=f"{user.username} has accepted your connection request!",
                related_object_id=connection.id,
                related_object_type='Connection'
            )
        return Response(ConnectionSerializer(connection).data)



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