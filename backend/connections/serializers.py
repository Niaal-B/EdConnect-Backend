from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from chat_app.models import ChatRoom
from connections.models import Connection
from mentors.models import MentorDetails
from mentors.serializers import SlotReadOnlySerializer, SlotSerializer
from students.models import StudentDetails
from users.models import User


class ConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connection
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ConnectionRequestSerializer(serializers.Serializer):
    mentor_id = serializers.IntegerField()

    def validate(self, attrs):
        request = self.context.get('request')
        student = request.user
        mentor_id = attrs.get('mentor_id')

        if student.role != 'student':
            raise ValidationError("Only students can send requests.")

        if not mentor_id:
            raise ValidationError({"mentor_id": "Mentor ID is required."})

        try:
            mentor = User.objects.get(id=mentor_id)
        except ObjectDoesNotExist:
            raise ValidationError({"mentor_id": "Mentor does not exist."})

        if mentor.role != 'mentor':
            raise ValidationError({"mentor_id": "The selected user is not a mentor."})

        try:
            mentor_details = MentorDetails.objects.get(user=mentor)
        except MentorDetails.DoesNotExist:
            raise ValidationError({"mentor_id": "Mentor profile does not exist."})

        if not mentor_details.countries or len(mentor_details.countries) == 0:
            raise ValidationError({"mentor_id": "Mentor has not set their country."})

        attrs['mentor'] = mentor
        return attrs


class ConnectionStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connection
        fields = ['status']

    def validate_status(self, value):
        allowed_choices = ['accepted', 'rejected']
        if value not in allowed_choices:
            raise serializers.ValidationError(
                f"Invalid status. Allowed values are: {', '.join(allowed_choices)}."
            )
        return value


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

class ConnectedStudentDetailsSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = StudentDetails
        fields = [
            'full_name',
            'email',
            'profile_picture',
        ]
    def get_full_name(self, obj):
        return obj.user.get_full_name()

class MentorConnectionSerializer(serializers.ModelSerializer):
    mentor_info = ConnectedMentorDetailsSerializer(source='mentor.mentor_profile')
    chat_room_id = serializers.SerializerMethodField()

    class Meta:
        model = Connection
        fields = ['id', 'mentor_info','chat_room_id']

    def get_chat_room_id(self, obj):
        """
        Retrieves the ID of the ChatRoom associated with this connection.
        'obj' here is a Connection instance.
        """
        try:
            chat_room = ChatRoom.objects.get(student=obj.student, mentor=obj.mentor)
            return str(chat_room.id) 
        except ChatRoom.DoesNotExist:
            # if any reson that when chat room not occurs
            return None
        except Exception as e:
            # handling this for any potntial err that will come in future
            print(f"Error retrieving chat room ID for connection {obj.id}: {e}")
            return None


class StudentConnectionSerializer(serializers.ModelSerializer):
    student_info = ConnectedStudentDetailsSerializer(source='student.student_profile')
    chat_room_id = serializers.SerializerMethodField()

    class Meta:
        model = Connection
        fields = ['id', 'student_info','chat_room_id']

    def get_chat_room_id(self, obj):
        """
        Retrieves the ID of the ChatRoom associated with this connection.
        'obj' here is a Connection instance.
        """
        try:
            chat_room = ChatRoom.objects.get(student=obj.student, mentor=obj.mentor)
            return str(chat_room.id) 
        except ChatRoom.DoesNotExist:
            # if any reson that when chat room not occurs
            return None
        except Exception as e:
            return None

