# from users.serializers import BaseUserRegistrationSerializer
# from students.models import StudentDetails
# from rest_framework import serializers
# from users.redis_utils import store_unverified_users


# class StudentRegistrationSerializer(BaseUserRegistrationSerializer):

#     education_level = serializers.CharField(
#         required=True,
#         help_text="Current education level (e.g., High School, Undergraduate)"
#     )
#     interests = serializers.ListField(
#         child=serializers.CharField(),
#         required=True,
#         help_text="List of academic/professional interests"
#     )

#     def create(self, validated_data):
#         #here we are storing the details in cache to verify the email
#         verification_token = store_unverified_users(validated_data)
#         return {'verification_token': verification_token, **validated_data}

        