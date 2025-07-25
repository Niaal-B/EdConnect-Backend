from django.urls import path
from mentors.views import (MentorLoginView,MentorProfileView,ProfilePictureView,
                        DocumentUploadView,PublicMentorListView,MentorSlotListCreateView,
                        MentorSlotCancelView,MentorStripeOnboardingView,MentorEarningsAPIView
)

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




    ]
