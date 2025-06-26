from rest_framework import serializers
from connections.models import Connection
from users.models import User
from students.models import StudentDetails  


class ConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connection
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class ConnectionRequestSerializer(serializers.Serializer):
    mentor_id = serializers.IntegerField()


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentDetails
        fields = ['profile_picture', 'preferred_countries', 'fields_of_interest']

class StudentBasicSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'student_profile']

class ConnectionWithStudentSerializer(serializers.ModelSerializer):
    student = StudentBasicSerializer(read_only=True)

    class Meta:
        model = Connection
        fields = ['id', 'student', 'status', 'created_at']