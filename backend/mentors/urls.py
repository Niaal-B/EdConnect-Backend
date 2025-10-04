from django.urls import path

from mentors.views import (DocumentUploadView, MentorDashboardStatsView,
                           MentorEarningsAPIView, MentorFeedbackView,
                           MentorLoginView, MentorProfileView,
                           MentorSlotCancelView, MentorSlotListCreateView,
                           MentorStripeOnboardingView, ProfilePictureView,
                           PublicMentorListView, UpcomingSessionsView)

urlpatterns = [
    path('login/',MentorLoginView.as_view(),name='mentor-login'),
    path('profile/', MentorProfileView.as_view(), name='mentor-profile'),
    path('profile/picture/', ProfilePictureView.as_view(), name='mentor-profile-picture'),
    path('documents/', DocumentUploadView.as_view(), name='mentor-documents'),
    path('mentors/public/', PublicMentorListView.as_view(), name='public-mentors'),
    path('slots/', MentorSlotListCreateView.as_view(), name='mentor-slot-list-create'),
    path('slots/<int:pk>/cancel/', MentorSlotCancelView.as_view(), name='mentor-slot-cancel'),
    path('stripe/onboard/', MentorStripeOnboardingView.as_view(), name='mentor-stripe-onboard'),
    path('earnings/', MentorEarningsAPIView.as_view(), name='mentor-earnings'),
    path('dashboard/stats',MentorDashboardStatsView.as_view(),name='mentor-dashboard'),
    path('upcoming-sessions/',UpcomingSessionsView.as_view(),name='sessions-dashboard'),
    path('feedback/', MentorFeedbackView.as_view(), name='mentor-feedback'),






    ]
