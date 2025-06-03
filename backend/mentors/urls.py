from django.urls import path
from mentors.views import MentorLoginView,MentorProfileView,ProfilePictureView,DocumentUploadView

urlpatterns = [
    path('login/',MentorLoginView.as_view(),name='mentor-login'),
    path('profile/', MentorProfileView.as_view(), name='mentor-profile'),
    path('profile/picture/', ProfilePictureView.as_view(), name='mentor-profile-picture'),
    path('documents/', DocumentUploadView.as_view(), name='mentor-documents'),

    ]
