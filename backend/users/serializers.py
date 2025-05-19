from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
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

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("Email already registered.")
        return attrs



class EmptySerializer(serializers.Serializer):
    pass