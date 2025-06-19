from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

def set_jwt_cookies(response, user):
    refresh = RefreshToken.for_user(user)
    cookie_kwargs = {
        'httponly': True,
        'secure': not settings.DEBUG,
        'samesite': 'Lax',
    }
    
    if settings.DEBUG:
        cookie_kwargs['domain'] = 'localhost'
    
    response.set_cookie(
        key='refresh_token',
        value=str(refresh),
        max_age=60*60*24*7,
        **cookie_kwargs
    )
    
    response.set_cookie(
        key='access_token',
        value=str(refresh.access_token),
        max_age=60*15,
        **cookie_kwargs
    )
    print(response,"this is response")    
    response['access_token'] = refresh.access_token
    return response