from django.urls import path

from .views import (BookingCancelAPIView, BookingCreateAPIView,
                    BookingStatusAPIView, MentorBookingsAPIView,
                    StudentBookingsAPIView, stripe_webhook,GenerateZegoTokenView,CompleteBookingView)

urlpatterns = [

    path('create/', BookingCreateAPIView.as_view(), name='booking-create'),
    path('status/<str:session_id>/', BookingStatusAPIView.as_view(), name='booking-status'),
    path('stripe-webhook/', stripe_webhook, name='stripe-webhook'),
    path('student-bookings/', StudentBookingsAPIView.as_view(), name='student-bookings'), 
    path('mentor-bookings/', MentorBookingsAPIView.as_view(), name='student-bookings'), 
    path('<uuid:pk>/cancel/', BookingCancelAPIView.as_view(), name='booking-cancel'),
    path('zego/generate-token',GenerateZegoTokenView.as_view(),name='zego-token'),
    path('<uuid:pk>/complete/', CompleteBookingView.as_view(), name='complete-booking'), 



]