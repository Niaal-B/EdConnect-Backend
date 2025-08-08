from django.shortcuts import render
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.exceptions import TokenError
import logging
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from auth.serializers import UserLoginSerializer
from users.utils import set_jwt_cookies
from rest_framework_simplejwt.tokens import AccessToken,RefreshToken
from .authentication import CookieJWTAuthentication
from django.conf import settings
from rest_framework.views import APIView
from users.models import User
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from users.tasks import send_reset_password_email
from auth.serializers import ForgotPasswordSerializer,ResetPasswordSerializer
from drf_yasg.utils import swagger_auto_schema
from mentors.models import MentorDetails
from students.models import StudentDetails

logger = logging.getLogger(__name__)

class VerifyAuthView(GenericAPIView):
    authentication_classes = [CookieJWTAuthentication]  

    permission_classes = [IsAuthenticated]  
    
    def get(self, request):

        
        
        return Response({
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "is_authenticated": True,
        }, status=status.HTTP_200_OK)


class CheckSessionView(GenericAPIView):
    authentication_classes = [CookieJWTAuthentication]  
    permission_classes = [IsAuthenticated]

    def get(self, request):

        try:
            user = request.user
            profile_picture_url = None

            # Fetch profile_picture based on role
            if user.role == "mentor":
                details = MentorDetails.objects.get(user=user)
                if details.profile_picture:
                    profile_picture_url = request.build_absolute_uri(details.profile_picture.url)

            elif user.role == "student":
                details = StudentDetails.objects.get(user=user)
                if details.profile_picture:
                    profile_picture_url = request.build_absolute_uri(details.profile_picture.url)

            response_data = {
                "valid": True,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "role": user.role,
                    "profile_picture": profile_picture_url,
                },
                "message": "session is valid"
            }
            return Response(response_data)

        except Exception as e:
            return Response(
                {
                    'valid': False,
                    "error": str(e),
                    'message': 'session validation Failed'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )


class CookieTokenRefreshView(GenericAPIView):
    """
    Custom token refresh view that works with httpOnly cookies
    """
    def post(self, request):
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT.get('AUTH_COOKIE_REFRESH', 'refresh_token'))
        
        if not refresh_token:
            logger.error("No refresh token in cookies")
            return Response(
                {'error': 'Refresh token is missing'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            refresh = RefreshToken(refresh_token)
            new_access_token = str(refresh.access_token)
            
            logger.debug("Successfully generated new access token")
            
            response = Response({
                'message': 'Token refreshed successfully'
            })
            
            # Set new access token cookie
            response.set_cookie(
                key=settings.SIMPLE_JWT['AUTH_COOKIE'],
                value=new_access_token,
                httponly=True,
                secure=settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
                samesite=settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                path=settings.SIMPLE_JWT.get('AUTH_COOKIE_PATH', '/')
            )
            
            return response
            
        except TokenError as e:
            logger.error(f"Token refresh failed: {str(e)}")
            return Response(
                {'error': 'Invalid refresh token', 'detail': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            logger.error(f"Unexpected error during refresh: {str(e)}")
            return Response(
                {'error': 'Token refresh failed', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




class ForgotPasswordView(GenericAPIView):
    serializer_class = ForgotPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"http://localhost:3000/reset-password/{uid}/{token}"
            send_reset_password_email.delay(email, reset_link)
        except User.DoesNotExist:
            pass  

        return Response({'message': 'a reset link has been sent.'}, status=200)

class ResetPasswordView(GenericAPIView):
    serializer_class = ResetPasswordSerializer
    def post(self, request, uidb64, token):
        password = request.data.get('new_password')
        if not password:
            return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)

            if not default_token_generator.check_token(user, token):
                return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(password)
            user.save()

            return Response({'message': 'Password reset successful'})
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({'error': 'Invalid reset link'}, status=status.HTTP_400_BAD_REQUEST)