from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class CookieJWTAuthentication(JWTAuthentication):
    """
    Authenticates against JWT in httpOnly cookie only
    """
    def authenticate(self, request):
        cookie_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])
        if not cookie_token:
            return None
        try:
            validated_token = self.get_validated_token(cookie_token)
            return self.get_user(validated_token), validated_token
        except InvalidToken:
            return None