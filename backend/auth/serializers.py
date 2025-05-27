from rest_framework import serializers
from django.contrib.auth import authenticate

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    def validate(self,attrs):
        user = authenticate(email=attrs['email'],password=attrs['password'])
        return user

