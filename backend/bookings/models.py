import uuid

from django.conf import settings
from django.db import models
from mentors.models import Slot


class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING_PAYMENT', 'Pending Payment'),
        ('CONFIRMED', 'Confirmed'),       
        ('CANCELLED', 'Cancelled'),          
        ('COMPLETED', 'Completed'),     
        ('CANCELED_BY_STUDENT_FULL_REFUND', 'Cancelled by Student (Full Refund)'), 
        ('CANCELED_BY_STUDENT_NO_REFUND', 'Cancelled by Student (No Refund)'),     
        ('CANCELED_BY_MENTOR', 'Cancelled by Mentor'),                          
        ('RESCHEDULED', 'Rescheduled'),         
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),  
        ('PAID', 'Paid'),         
        ('FAILED', 'Failed'),    
        ('REFUNDED', 'Refunded'), 
        ('REFUND_FAILED', 'Refund Failed'),  
        ('NO_REFUND', 'No Refund Issued'), 
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_bookings')
    mentor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentor_received_bookings')
    slot = models.ForeignKey(Slot, on_delete=models.SET_NULL, null=True, blank=True, related_name='booking')

    booked_start_time = models.DateTimeField()
    booked_end_time = models.DateTimeField()
    booked_fee = models.DecimalField(max_digits=10, decimal_places=2)
    booked_timezone = models.CharField(max_length=50)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING_PAYMENT')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')

    stripe_checkout_session_id = models.CharField(
        max_length=255, null=True, blank=True, unique=True,
        help_text="Stripe Checkout Session ID for this booking's payment"
    )
    stripe_payment_intent_id = models.CharField(
        max_length=255, null=True, blank=True, unique=True,
        help_text="Stripe Payment Intent ID once payment is confirmed"
    )

    cancelled_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='cancelled_bookings') # New
    cancelled_at = models.DateTimeField(null=True, blank=True)                                                                          # New
    cancellation_reason = models.TextField(null=True, blank=True)                                                                       # New (optional field for the user to provide a reason)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"

    def __str__(self):
        return f"Booking {self.id} | {self.student.username} with {self.mentor.username} ({self.status})"



class BookingCalendarEvent(models.Model):
    """
    Stores the Google Calendar Event ID for a specific user and booking.
    This allows managing calendar events for both mentor and student separately.
    """
    booking = models.ForeignKey(
        'Booking', 
        on_delete=models.CASCADE,
        related_name='calendar_events',
        verbose_name="Related Booking"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="User Owning the Calendar Event"
    )
    google_event_id = models.CharField(
        max_length=255,
        verbose_name="Google Calendar Event ID",
        help_text="ID of the event in the user's Google Calendar"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    class Meta:
        unique_together = ('booking', 'user')
        verbose_name = "Booking Calendar Event"
        verbose_name_plural = "Booking Calendar Events"

    def __str__(self):
        return f"Event for Booking {self.booking.id} ({self.user.username})"


class Feedback(models.Model):
    booking = models.OneToOneField(
        Booking, 
        on_delete=models.CASCADE, 
        related_name='feedback',
        help_text="The booking this feedback is for."
    )
    rating = models.PositiveSmallIntegerField(
        help_text="Rating given by the student (1 to 5)."
    )
    comment = models.TextField(
        blank=True,
        help_text="Optional comments from the student."
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_feedback',
        help_text="The user who submitted this feedback."
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for Booking {self.booking.id} - Rating: {self.rating}"

    class Meta:
        verbose_name_plural = "Feedback"