from django.shortcuts import render
from rest_framework.generics import ListAPIView
from auth.authentication import CookieJWTAuthentication
from rest_framework.permissions import IsAuthenticated
from .serializers import NotificationSerializer
from .models import Notification

class NotificationListView(ListAPIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)