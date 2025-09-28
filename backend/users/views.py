import json

from django.conf import settings
from mentors.models import MentorDetails
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from students.models import StudentDetails
from users.models import User
from users.redis_utils import redis_client, store_unverified_user
from users.serializers import EmptySerializer, UserRegistrationSerializer
from users.tasks import send_verification_email
from users.utils import set_jwt_cookies


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
                

            if user.role == 'mentor':
                MentorDetails.objects.create(user=user)

            else:
                StudentDetails.objects.create(user=user)
                
            response = Response({"status": "verified",'role': user.role}, status=status.HTTP_200_OK)
            return Response({
            "message": "User registered successfully. OTP sent to email.",
        }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass

        response = Response(
            {"message": "Logged out successfully."},
            status=status.HTTP_200_OK
        )

        cookie_kwargs = {
            "path": "/",
            "domain": None,  
            "samesite": "None" if not settings.DEBUG else "Lax",
        }

        response.delete_cookie("access_token", **cookie_kwargs)
        response.delete_cookie("refresh_token", **cookie_kwargs)

        return response
