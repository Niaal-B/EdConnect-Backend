from rest_framework import serializers
from django.contrib.auth import authenticate

class StudentLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self,attrs):
        user = authenticate(user=attrs['email'],password=attrs['password'])
        if not user or user.role !='student':
            raise serializers.ValidationError("Invalid Student credentials")

        return user
        