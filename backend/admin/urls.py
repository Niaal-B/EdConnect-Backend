from django.urls import path

from admin.views import (AdminBookingsView, AdminDashboardStatsView,
                         AdminLoginView, AdminMentorFeedbackList,
                         ApproveRejectMentorView, MentorVerificationDetailView,
                         PendingMentorVerificationsView, RejectedMentorsView,
                         UpdateVerificationStatusView, UserListView,
                         UserStatusUpdateView, VerifiedMentorsView)

urlpatterns = [
    path('login/',AdminLoginView.as_view(),name='admin-login'),
    path('users/',UserListView.as_view(),name='admin-users'),
    path('users/<int:user_id>/status/', UserStatusUpdateView.as_view(), name='user-status-update'),
    path('mentors/pending/', PendingMentorVerificationsView.as_view(), name='pending-mentors'),
    path('mentors/verified/', VerifiedMentorsView.as_view(), name='verified-mentors'),
    path('mentors/rejected/', RejectedMentorsView.as_view(), name='rejected-mentors'),
    path('mentors/<int:id>/', MentorVerificationDetailView.as_view(), name='mentor-detail'),
    path('mentors/<int:mentor_id>/approve-reject/', ApproveRejectMentorView.as_view(), name='approve-reject-mentor'),
    path('mentors/<int:mentor_id>/status/', UpdateVerificationStatusView.as_view(), name='update-mentor-status'),
    path('dashboard/stats/', AdminDashboardStatsView.as_view(), name='admin-dashboard-stats'),
    path('bookings/', AdminBookingsView.as_view(), name='admin-bookings'), 
    path('feedback/mentors/', AdminMentorFeedbackList.as_view(), name='admin-mentor-feedback-list'),


]
