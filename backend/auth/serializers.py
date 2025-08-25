from django.contrib.auth import authenticate
from rest_framework import serializers


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    def validate(self,attrs):
        user = authenticate(email=attrs['email'],password=attrs['password'])
        return user

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)