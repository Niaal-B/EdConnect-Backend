from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

def set_jwt_cookies(response, user):
    refresh = RefreshToken.for_user(user)
    response.set_cookie(
        key='refresh_token',
        value=str(refresh),
        httponly=True,
        secure=not settings.DEBUG,
        samesite='Lax',
        max_age=60*60*24*7  # 7 days
    )
    response.set_cookie(
        key='access_token',
        value=str(refresh.access_token),
        httponly=True,
        secure=not settings.DEBUG,
        samesite='Lax',
        max_age=60*15  # 15 minutes
    )
    return response
