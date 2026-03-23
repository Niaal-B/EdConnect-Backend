from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


def set_jwt_cookies(response, user):
    refresh = RefreshToken.for_user(user)
    
    is_production = not settings.DEBUG
    
    cookie_kwargs = {
        'httponly': True,
        'secure': True,  # Set to True for HTTPS
        'samesite': 'None', # Required for cross-site (Vercel to AWS)
        'path': '/', 
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
    
    return response