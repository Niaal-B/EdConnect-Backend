from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


def set_jwt_cookies(response, user):
    refresh = RefreshToken.for_user(user)
    cookie_kwargs = {
        'httponly': True,
        'secure': not settings.DEBUG,
        'samesite': 'None' if not settings.DEBUG else 'Lax',
    }
    

    response.set_cookie(
        key='refresh_token',
        value=str(refresh),
        max_age=60*60*24*7,
        **cookie_kwargs
    )
    
    response.set_cookie(
        key='access_token',
        value=str(refresh.access_token),
        max_age=60*1,
        **cookie_kwargs
    )
    
    response['access_token'] = refresh.access_token
    return response