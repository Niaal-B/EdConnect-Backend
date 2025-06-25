from django.urls import path
from connections.views import RequestConnectionView, PendingRequestsView, ManageConnectionStatus

urlpatterns = [
    path('request/', RequestConnectionView.as_view(), name='connection-request'),
    path('pending/', PendingRequestsView.as_view(), name='pending-requests'),
    path('<int:pk>/', ManageConnectionStatus.as_view(), name='manage-connection'),
]
