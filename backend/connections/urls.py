from django.urls import path
from connections.views import (RequestConnectionView, PendingRequestsView, ManageConnectionStatus,ListConnectionsView,
CancelConnectionView
)

urlpatterns = [

    path('', ListConnectionsView.as_view(), name='list-connections'),
    path('request/', RequestConnectionView.as_view(), name='connection-request'),
    path('pending/', PendingRequestsView.as_view(), name='pending-requests'),
    path('<int:pk>/', ManageConnectionStatus.as_view(), name='manage-connection'),
    path('<int:pk>/cancel/', CancelConnectionView.as_view(), name='cancel-connection'),  # ← NEW


]
