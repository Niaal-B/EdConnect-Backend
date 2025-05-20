from rest_framework import serializers
from django.contrib.auth import authenticate

class MentorLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    def validate(self,attrs):
        user = authenticate(email=attrs['email'],password=attrs['password'])
        print(user,"this is user monna")
        if not user or user.role != 'mentor':
            raise serializers.ValidationError("Invalid mentor credentials")

        return user

