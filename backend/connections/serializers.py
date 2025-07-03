from rest_framework import serializers
from connections.models import Connection
from users.models import User
from students.models import StudentDetails  
from mentors.serializers import SlotSerializer,SlotReadOnlySerializer
from mentors.models import MentorDetails

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



class ConnectedMentorDetailsSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')
    slots = SlotReadOnlySerializer(source='user.slots', many=True)

    class Meta:
        model = MentorDetails
        fields = [
            'full_name',
            'email',
            'profile_picture',
            'bio',
            'expertise',
            'slots',
        ]
    def get_full_name(self, obj):
        return obj.user.get_full_name()

class MentorConnectionSerializer(serializers.ModelSerializer):
    mentor_info = ConnectedMentorDetailsSerializer(source='mentor.mentor_profile')

    class Meta:
        model = Connection
        fields = ['id', 'mentor_info']