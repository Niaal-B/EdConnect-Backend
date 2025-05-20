from django.urls import path
from mentors.views import MentorLoginView

urlpatterns = [
    path('login/',MentorLoginView.as_view(),name='mentor-login')
]
