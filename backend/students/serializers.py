from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from students.models import StudentDetails
from users.serializers import UserSerializer
from mentors.models import MentorDetails
from bookings.models import Booking

class StudentLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self,attrs):
        user = authenticate(email=attrs['email'],password=attrs['password'])
        if not user or user.role !='student':
            raise serializers.ValidationError("Invalid Student credentials")

        return user

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
            'profile_picture',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        


