from django.urls import path

from connections.views import (CancelConnectionView, ListConnectionsView,
                               ManageConnectionStatus, MyMentorsView,
                               MyStudentsView, PendingRequestsView,
                               RequestConnectionView)

urlpatterns = [

    path('', ListConnectionsView.as_view(), name='list-connections'),
    path('request/', RequestConnectionView.as_view(), name='connection-request'),
    path('pending/', PendingRequestsView.as_view(), name='pending-requests'),
    path('<int:pk>/', ManageConnectionStatus.as_view(), name='manage-connection'),
    path('<int:pk>/cancel/', CancelConnectionView.as_view(), name='cancel-connection'),
    path('my-mentors/', MyMentorsView.as_view(), name='my-mentors'),
    path('my-students/', MyStudentsView.as_view(), name='my-students'),




]
