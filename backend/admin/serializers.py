from django.contrib.auth import authenticate
from mentors.models import MentorDetails, VerificationDocument
from rest_framework import serializers
from students.models import StudentDetails
from mentors.models import MentorDetails,Slot
from django.contrib.auth import get_user_model
from bookings.models import Booking,Feedback

User = get_user_model()

class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self,attrs):
        user = authenticate(email=attrs['email'],password=attrs['password'])
        if not user or not user.is_staff:
            raise serializers.ValidationError("Invalid admin credentials")


        return user

class VerificationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationDocument
        fields = ['id', 'document_type', 'file', 'uploaded_at', 'is_approved']
        read_only_fields = ['id', 'uploaded_at']

class MentorVerificationSerializer(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField()
    full_name = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = MentorDetails
        fields = [
            'id', 'full_name', 'email', 'bio', 'phone', 
            'expertise', 'experience_years', 'is_verified',
            'verification_status', 'rejection_reason', 'last_status_update',
            'profile_picture', 'documents'
        ]
    
    def get_documents(self, obj):
        documents = obj.user.documents.all()
        return VerificationDocumentSerializer(documents, many=True).data

class MentorApprovalSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    reason = serializers.CharField(required=False, allow_blank=True)




class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class StudentDetailsSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    
    class Meta:
        model = StudentDetails
        fields = [
            'id', 
            'user', 
            'education_level', 
            'fields_of_interest', 
            'mentorship_preferences', 
            'preferred_countries', 
            'interested_universities', 
            'additional_notes', 
            'profile_picture'
        ]

class MentorDetailsSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = MentorDetails
        fields = [
            'id', 
            'user', 
            'profile_picture', 
            'bio', 
            'expertise', 
            'experience_years'
        ]

class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ['id', 'start_time', 'end_time', 'fee', 'timezone', 'status']

class BookingSerializer(serializers.ModelSerializer):
    slot_info = SlotSerializer(source='slot', read_only=True)
    student_details = serializers.SerializerMethodField()
    mentor_details = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'student', 'mentor', 'slot', 'student_details', 'mentor_details',
            'booked_start_time', 'booked_end_time', 'booked_fee', 'booked_timezone',
            'status', 'payment_status', 'stripe_checkout_session_id', 
            'stripe_payment_intent_id', 'created_at', 'updated_at','slot_info'
        ]

    def get_student_details(self, obj):
        profile = getattr(obj.student, 'student_profile', None)
        if profile:
            return StudentDetailsSerializer(profile).data
        return None
    
    def get_mentor_details(self, obj):
        profile = getattr(obj.mentor, 'mentor_profile', None)
        if profile:
            return MentorDetailsSerializer(profile).data
        return None


class AdminMentorFeedbackSerializer(serializers.ModelSerializer):
    booking_id = serializers.UUIDField(source='booking.id', read_only=True)
    booked_start_time = serializers.DateTimeField(source='booking.booked_start_time', read_only=True)
    booked_end_time = serializers.DateTimeField(source='booking.booked_end_time', read_only=True)
    
    mentor_details = serializers.SerializerMethodField()
    student_details = serializers.SerializerMethodField()

    class Meta:
        model = Feedback
        fields = [
            'id', 'booking_id', 'rating', 'comment', 'submitted_at',
            'booked_start_time', 'booked_end_time', 
            'mentor_details', 'student_details',
        ]
        read_only_fields = fields

    def get_mentor_details(self, obj):
        profile = getattr(obj.booking.mentor, 'mentor_profile', None)
        if profile:
            from .serializers import MentorDetailsSerializer 
            return MentorDetailsSerializer(profile).data
        return None
    
    def get_student_details(self, obj):
        profile = getattr(obj.submitted_by, 'student_profile', None)
        if profile:
            from .serializers import StudentDetailsSerializer
            return StudentDetailsSerializer(profile).data
        return None