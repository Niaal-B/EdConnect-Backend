from rest_framework import serializers
from bookings.models import Booking
from mentors.models import Slot

from students.serializers import StudentDetailsSerializer
from mentors.serializers import MentorProfileSerializer


class BasicSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ['id', 'start_time', 'end_time', 'fee', 'timezone', 'status']

class BookingSerializer(serializers.ModelSerializer):
    student_profile_info = StudentDetailsSerializer(source='student.student_profile', read_only=True)
    mentor_profile_info = MentorProfileSerializer(source='mentor.mentor_profile', read_only=True)
    slot_info = BasicSlotSerializer(source='slot', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id',
            'student',
            'mentor',
            'slot',
            'student_profile_info',
            'mentor_profile_info',
            'slot_info',
            'booked_start_time',
            'booked_end_time',
            'booked_fee',
            'booked_timezone',
            'status',
            'payment_status',
            'stripe_checkout_session_id',
            'stripe_payment_intent_id',
            'created_at',
            'updated_at'
        ]

        read_only_fields = [
            'id',
            'student',
            'student_profile_info', 
            'mentor',
            'mentor_profile_info', 
            'slot_info', 
            'booked_start_time',
            'booked_end_time',
            'booked_fee',
            'booked_timezone',
            'status',
            'payment_status',
            'stripe_checkout_session_id',
            'stripe_payment_intent_id',
            'created_at',
            'updated_at'
        ]


