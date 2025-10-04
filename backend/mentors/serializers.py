from datetime import timedelta

from django.contrib.auth import authenticate
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from rest_framework import serializers

from bookings.models import Booking
from mentors.models import Education, MentorDetails, Slot, VerificationDocument
from students.models import StudentDetails
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User 
        fields = ['id', 'email', 'username', 'role'] 

class MentorLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    def validate(self,attrs):
        user = authenticate(email=attrs['email'],password=attrs['password'])
        if not user or user.role != 'mentor':
            raise serializers.ValidationError("Invalid mentor credentials")

        return user

class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = '__all__'
        read_only_fields = ['mentor']

class VerificationDocumentSerializer(serializers.ModelSerializer):
    file = serializers.FileField(
        required=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    
    class Meta:
        model = VerificationDocument
        fields = ['file']

class MentorProfileSerializer(serializers.ModelSerializer):
    educations = EducationSerializer(many=True, read_only=True)
    documents = serializers.SerializerMethodField()
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MentorDetails
        fields = '__all__'
        read_only_fields = ['user', 'is_verified']

    def get_documents(self, obj):
        request = self.context.get('request', None)
        return [
            {
                "id": doc.id,
                "document_type": doc.document_type,
                "file": request.build_absolute_uri(doc.file.url) if request else doc.file.url,
                "is_approved": doc.is_approved,
                "uploaded_at": doc.uploaded_at,
            }
            for doc in obj.user.documents.all()
        ]


class MentorProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorDetails
        fields = ['bio', 'phone', 'expertise',  'countries', 'courses','experience_years']

class ProfilePictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorDetails
        fields = ['profile_picture']
        extra_kwargs = {
            'profile_picture': {
                'required': True,
                'validators': [FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
            }
        }

class PublicMentorSerializer(serializers.ModelSerializer):
    educations = EducationSerializer(many=True, read_only=True)  
    username = serializers.CharField(source='user.username', read_only=True)
    

    class Meta:
        model = MentorDetails
        fields = [
            'id','username','user_id', 'bio', 'expertise','countries','courses','experience_years', 
            'educations', 'is_verified', 'profile_picture' 
        ]
        read_only_fields = ['is_verified']



class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ['id', 'mentor', 'start_time', 'end_time', 'fee', 'timezone', 'status', 'created_at']
        read_only_fields = ['id', 'mentor', 'status', 'created_at']

    def validate(self, data):
        start = data['start_time']
        end = data['end_time']

        if start >= end:
            raise serializers.ValidationError("End time must be after start time.")

        duration = (end - start).total_seconds() / 60
        if duration < 15 or duration > 120:
            raise serializers.ValidationError("Slot duration must be between 15 minutes and 2 hours.")

        if start <= timezone.now():
            raise serializers.ValidationError("Slot must be in the future.")

        mentor = self.context['request'].user
        if Slot.objects.filter(mentor=mentor, start_time__lt=end, end_time__gt=start).exists():
            raise serializers.ValidationError("This slot overlaps with an existing slot.")

        return data

    def create(self, validated_data):
        validated_data['mentor'] = self.context['request'].user
        return super().create(validated_data)


class SlotReadOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ['id', 'start_time', 'end_time', 'fee', 'timezone', 'status']
        read_only_fields = fields

class StudentsDetailsForBookingSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.firstname", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = StudentDetails
        fields = [
            "full_name",
            "email",
            "profile_picture",
        ]


class UpcomingBookingSerializer(serializers.ModelSerializer):
    student_details = StudentsDetailsForBookingSerializer(source="mentor.mentor_profile", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "booked_start_time",
            "booked_end_time",
            "status",
            "student_details",
        ]