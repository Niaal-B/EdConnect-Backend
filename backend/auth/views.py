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
            response_data = {
                "valid": True,  # Changed from string "True" to boolean
                "user": {
                    "id": request.user.id,  
                    "email": request.user.email,
                    "username": request.user.username,
                    "role": request.user.role
                },
                "message": "session is valid"
            }
            return Response(response_data)

        except Exception as e:
            return Response(
                {
                    'valid': False,  # Changed from string "False" to boolean
                    "error": str(e),
                    'message': 'session validation Failed'
                },
                status=status.HTTP_401_UNAUTHORIZED  # Changed from 500 to 401
            )


class CookieTokenRefreshView(GenericAPIView):
    """
    Custom token refresh view that works with httpOnly cookies
    """
    def post(self, request):
        # Get refresh token from cookie
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