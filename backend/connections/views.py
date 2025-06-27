from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from connections.models import Connection
from .serializers import ConnectionSerializer,ConnectionRequestSerializer,ConnectionWithStudentSerializer
from auth.authentication import CookieJWTAuthentication
from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404
from users.models import User
from django.core.exceptions import ValidationError, ObjectDoesNotExist



class RequestConnectionView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=ConnectionRequestSerializer,
        responses={201: ConnectionSerializer, 400: dict, 403: dict}
    )
    def post(self, request):
        try:
            serializer = ConnectionRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            mentor_id = serializer.validated_data.get('mentor_id')
            student = request.user

            if student.role != 'student':
                return Response({'detail': 'Only students can send requests.'}, status=status.HTTP_403_FORBIDDEN)

            if not mentor_id:
                return Response({'detail': 'Mentor ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                mentor = User.objects.get(id=mentor_id)
            except ObjectDoesNotExist:
                return Response({'detail': 'Mentor does not exist.'}, status=status.HTTP_404_NOT_FOUND)

            if mentor.role != 'mentor':
                return Response({'detail': 'The selected user is not a mentor.'}, status=status.HTTP_400_BAD_REQUEST)

            if Connection.objects.filter(student=student, mentor=mentor).exists():
                return Response({'detail': 'Connection already exists.'}, status=status.HTTP_400_BAD_REQUEST)

            connection = Connection.objects.create(student=student, mentor=mentor)
            return Response(ConnectionSerializer(connection).data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Catch any unexpected server errors
            return Response({'detail': f'Server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

        connection.status = status_choice
        connection.save()
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
        return Response({'detail': 'Connection request cancelled successfully.'}, status=status.HTTP_204_NO_CONTENT)