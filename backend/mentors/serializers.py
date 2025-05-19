from users.serializers import BaseUserRegistrationSerializer
from mentors.models import MentorDetails
from rest_framework import serializers
from users.redis_utils import store_unverified_users

class MentorRegistrationSerializer(BaseUserRegistrationSerializer):
    # Mentor-specific fields
    expertise = serializers.ListField(
        child=serializers.CharField(),
        required=True
    )
    experience_years = serializers.IntegerField(required=True, min_value=0)
    availability = serializers.DictField(required=True)
    verification_document = serializers.FileField(
        required=True,
        help_text="Upload verification document (PDF, JPG, PNG)",
        style={'input_type': 'file'}  
    )

    def create(self, validated_data):
        #here we are storing the details in cache to verify the email
        verification_token = store_unverified_users(validated_data)
        return {'verification_token': verification_token, **validated_data}
    