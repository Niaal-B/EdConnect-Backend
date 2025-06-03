from rest_framework import serializers
from django.contrib.auth import authenticate
from mentors.models import MentorDetails,Education,VerificationDocument
from django.core.validators import FileExtensionValidator

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
    documents = VerificationDocumentSerializer(many=True, read_only=True)
    
    class Meta:
        model = MentorDetails
        fields = '__all__'
        read_only_fields = ['user', 'is_verified']

class MentorProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorDetails
        fields = ['bio', 'phone', 'expertise', 'experience_years']

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