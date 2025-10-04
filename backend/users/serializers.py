from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from mentors.serializers import MentorProfileSerializer
from users.models import User
from users.redis_utils import get_and_delete_unverified_user


class UserRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    username = serializers.CharField(max_length=150, required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        if not value.isalnum():  
            raise serializers.ValidationError("Username must be alphanumeric.")
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value

    def validate_password(self, value):
        validate_password(value) 
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if value.isdigit():
            raise serializers.ValidationError("Password cannot be entirely numeric.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        return attrs


class EmptySerializer(serializers.Serializer):
    pass


class UserSerializer(ModelSerializer):
    mentor_profile = MentorProfileSerializer(read_only=True) 

    class Meta:
        model = User
        fields = ['id', 'username', 'email','role','created_at','is_active','mentor_profile']

