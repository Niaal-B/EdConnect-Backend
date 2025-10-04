from rest_framework import serializers

from bookings.models import Booking, Feedback
from mentors.models import Slot
from mentors.serializers import MentorProfileSerializer
from students.serializers import StudentDetailsSerializer


class BasicSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ['id', 'start_time', 'end_time', 'fee', 'timezone', 'status']

class BookingSerializer(serializers.ModelSerializer):
    mentor_profile_info = MentorProfileSerializer(source='mentor.mentor_profile', read_only=True)
    slot_info = BasicSlotSerializer(source='slot', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id',
            'student',
            'mentor',
            'slot',
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

class MentorBookingsSerializer(serializers.ModelSerializer):
    student_profile_info = StudentDetailsSerializer(source='student.student_profile', read_only=True)
    slot_info = BasicSlotSerializer(source='slot', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id',
            'student',
            'mentor',
            'slot',
            'student_profile_info',
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




class FeedbackSerializer(serializers.ModelSerializer):
    student_details = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = ['booking', 'rating', 'comment', 'submitted_by', 'submitted_at', 'student_details']
        read_only_fields = ['submitted_by', 'submitted_at', 'student_details']

    def get_student_details(self, obj):
        profile = getattr(obj.submitted_by, 'student_profile', None)
        if profile:
            return StudentDetailsSerializer(profile).data
        return None