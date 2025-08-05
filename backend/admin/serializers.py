from rest_framework import serializers
from django.contrib.auth import authenticate
from mentors.models import MentorDetails, VerificationDocument


class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self,attrs):
        user = authenticate(email=attrs['email'],password=attrs['password'])
        print(user)
        if not user or not user.is_staff:
            raise serializers.ValidationError("Invalid admin credentials")


        return user

class VerificationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationDocument
        fields = ['id', 'document_type', 'file', 'uploaded_at', 'is_approved']
        read_only_fields = ['id', 'uploaded_at']

class MentorVerificationSerializer(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField()
    full_name = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = MentorDetails
        fields = [
            'id', 'full_name', 'email', 'bio', 'phone', 
            'expertise', 'experience_years', 'is_verified',
            'verification_status', 'rejection_reason', 'last_status_update',
            'profile_picture', 'documents'
        ]
    
    def get_documents(self, obj):
        documents = obj.user.documents.all()
        return VerificationDocumentSerializer(documents, many=True).data

class MentorApprovalSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    reason = serializers.CharField(required=False, allow_blank=True)