from rest_framework import generics, status
from rest_framework.response import Response
from users.redis_utils import store_unverified_user
from users.tasks import send_verification_email
from users.serializers import UserRegistrationSerializer,EmptySerializer
from rest_framework.views import APIView
from users.redis_utils import redis_client
import json
from users.models import User

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_data = {
            'email': serializer.validated_data['email'],
            'username': serializer.validated_data['username'],
            'password': serializer.validated_data['password'],
            'role': serializer.validated_data['role']
        }
        
        try:
            verification_token = store_unverified_user(user_data)
            send_verification_email.delay(
                email=user_data['email'],
                token=verification_token
            )
            return Response({"status": "verification_pending"}, status=202)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class VerifyEmailView(generics.GenericAPIView):
    serializer_class = EmptySerializer
    
    def post(self, request, token):
        try:
            data = redis_client.get(f"unverified:{token}")
            if not data:
                return Response({"error": "Invalid token"}, status=400)
                
            user_data = json.loads(data)
            user = User.objects.create_user(
                email=user_data['email'],
                username=user_data['username'],
                password=user_data['password'],
                role=user_data['role'],
                is_active=True
            )
            redis_client.delete(f"unverified:{token}")
            return Response({"status": "verified"})
        except Exception as e:
            return Response({"error": str(e)}, status=400)