import datetime
import os
from datetime import timedelta

import requests
from api.models import UserGoogleTokens
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from mentors.models import MentorDetails
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from students.models import StudentDetails
from users.models import User
from users.utils import set_jwt_cookies

User = get_user_model() 

class GoogleLoginCallbackView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        code = request.GET.get('code')
        error = request.GET.get('error')
        state = request.GET.get('state')

        if error:
            return Response({'error': f'Google OAuth Error: {error}'}, status=status.HTTP_400_BAD_REQUEST)

        if not code:
            return Response({'error': 'Authorization code not provided.'}, status=status.HTTP_400_BAD_REQUEST)

        desired_role = None
        if state:
            if state == 'student':
                desired_role = 'student'
            elif state == 'mentor':
                desired_role = 'mentor'
            else:
                return Response({'error': 'Unexpected role specified in Google OAuth flow.'}, status=status.HTTP_400_BAD_REQUEST)

        if not desired_role:
            return Response({'error': 'Role not specified in Google OAuth flow.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id'],
                        "client_secret": settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['secret'],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI")],
                    }
                },
                scopes=settings.SOCIALACCOUNT_PROVIDERS['google']['SCOPE'],
                redirect_uri=os.getenv("GOOGLE_REDIRECT_URI"),
            )

            token_response = flow.fetch_token(code=code)
            credentials = flow.credentials

            token_type = token_response.get('token_type', 'Bearer')

            google_access_token = credentials.token
            google_refresh_token = credentials.refresh_token 
            google_expires_at = credentials.expiry


        except Exception as e:
            return Response({'error': f'Failed to exchange code for tokens: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
            headers = {'Authorization': f'Bearer {google_access_token}'}
            user_info_response = requests.get(user_info_url, headers=headers)
            user_info_response.raise_for_status()
            user_info = user_info_response.json()

            email = user_info.get('email')
            first_name = user_info.get('given_name', '')
            last_name = user_info.get('family_name', '')
            google_id = user_info.get('id')

            if not email:
                return Response({'error': 'Google user email not found.'}, status=status.HTTP_400_BAD_REQUEST)

        except requests.exceptions.RequestException as e:
            return Response({'error': f'Failed to fetch user info from Google: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        user, created = User.objects.get_or_create(email=email)

        if created:
            user.first_name = first_name
            user.last_name = last_name
            user.username = email 
            user.set_unusable_password() 
            user.role = desired_role
            user.save()

            if user.role == 'mentor':
                MentorDetails.objects.create(user=user)
            else:
                StudentDetails.objects.create(user=user)

        else: 
            if user.role != desired_role:
                return Response({'error': f"Existing user '{email}' has role '{user.role}' and tried to sign in as '{desired_role}'. Role mismatch. Please use the correct login path or contact support."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            defaults_dict = {
                'access_token': google_access_token,
                'expires_in': google_expires_at,
                'token_type': token_type,
            }

            if google_refresh_token:
                defaults_dict['refresh_token'] = google_refresh_token

            user_google_tokens, tokens_created = UserGoogleTokens.objects.update_or_create(
                user=user,
                defaults=defaults_dict
            )

        except Exception as e:
            return Response({'error': f'Failed to store Google tokens: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            if user.role == 'student':
                frontend_redirect_url = f"{settings.FRONTEND_URL}/student/dashboard"
            elif user.role == 'mentor':
                frontend_redirect_url = f"{settings.FRONTEND_URL}/mentor/dashboard"
            else:
                frontend_redirect_url = f"{settings.FRONTEND_URL}/dashboard"


            response = redirect(frontend_redirect_url)

            final_response = set_jwt_cookies(response, user)

            return final_response 

        except Exception as e:
            return Response({'error': 'Failed to set JWTs or redirect.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        return Response({'error': 'An unhandled server error occurred during login callback processing.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
def hello_api(request):
    return JsonResponse({"message": "Hello from Django API!"})