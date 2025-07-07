from django.db import models
from django.conf import settings
import uuid
from mentors.models import Slot

class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING_PAYMENT', 'Pending Payment'),
        ('CONFIRMED', 'Confirmed'),       
        ('CANCELLED', 'Cancelled'),          
        ('COMPLETED', 'Completed'),            
        ('RESCHEDULED', 'Rescheduled'),         
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),  
        ('PAID', 'Paid'),         
        ('FAILED', 'Failed'),    
        ('REFUNDED', 'Refunded'), 
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_bookings')
    mentor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentor_received_bookings')
    slot = models.ForeignKey(Slot, on_delete=models.SET_NULL, null=True, blank=True, related_name='booking')

    booked_start_time = models.DateTimeField()
    booked_end_time = models.DateTimeField()
    booked_fee = models.DecimalField(max_digits=10, decimal_places=2)
    booked_timezone = models.CharField(max_length=50)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_PAYMENT')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')

    stripe_checkout_session_id = models.CharField(
        max_length=255, null=True, blank=True, unique=True,
        help_text="Stripe Checkout Session ID for this booking's payment"
    )
    stripe_payment_intent_id = models.CharField(
        max_length=255, null=True, blank=True, unique=True,
        help_text="Stripe Payment Intent ID once payment is confirmed"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"

    def __str__(self):
        return f"Booking {self.id} | {self.student.username} with {self.mentor.username} ({self.status})"

