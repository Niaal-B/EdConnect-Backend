from django.urls import path

from .views import NotificationListView

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification"),    
    ]
