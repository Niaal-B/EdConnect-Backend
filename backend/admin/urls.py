from django.urls import path
from admin.views import (AdminLoginView,
                        UserListView,UserStatusUpdateView,
                        PendingMentorVerificationsView,
                        MentorVerificationDetailView,
                        ApproveRejectMentorView,
                        UpdateVerificationStatusView
                        )


urlpatterns = [
    path('login/',AdminLoginView.as_view(),name='admin-login'),
    path('users/',UserListView.as_view(),name='admin-users'),
    path('users/<int:user_id>/status/', UserStatusUpdateView.as_view(), name='user-status-update'),
    path('mentors/pending/', PendingMentorVerificationsView.as_view(), name='pending-mentors'),
    path('mentors/<int:id>/', MentorVerificationDetailView.as_view(), name='mentor-detail'),
    path('mentors/<int:mentor_id>/approve-reject/', ApproveRejectMentorView.as_view(), name='approve-reject-mentor'),
    path('mentors/<int:mentor_id>/status/', UpdateVerificationStatusView.as_view(), name='update-mentor-status'),
]
