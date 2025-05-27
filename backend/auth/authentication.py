# api/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from django.conf import settings

class CookieJWTAuthentication(JWTAuthentication):
    """
    Authenticates against JWT in httpOnly cookie only
    """
    def authenticate(self, request):
        cookie_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])
        if not cookie_token:
            return None
            print("No cookie token")
        try:
            validated_token = self.get_validated_token(cookie_token)
            print("hey this is validated token",validated_token)
            return self.get_user(validated_token), validated_token
        except InvalidToken:
            print("Man this is invalid")
            return None