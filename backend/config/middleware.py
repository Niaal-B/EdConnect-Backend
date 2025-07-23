from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model

User = get_user_model()

@database_sync_to_async
def get_user_from_token(token_key):
    """
    Attempts to get a user from a JWT token.
    This function runs in a separate thread (via database_sync_to_async)
    because JWT validation and user lookup can be blocking.
    """
    try:
        access_token = AccessToken(token_key)
        user_id = access_token['user_id']
        
        user = User.objects.get(id=user_id)
        return user
    except (InvalidToken, TokenError, User.DoesNotExist) as e:
        print(f"JWT validation failed or user not found: {e}")
        return AnonymousUser() # Return AnonymousUser if validation fails

class JWTAuthMiddleware:
    """
    Custom Channels middleware to authenticate users using JWT from HttpOnly cookies.
    This middleware will populate scope["user"] with the authenticated user.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'websocket':
            headers = dict(scope['headers'])
            cookie_header = headers.get(b'cookie', b'').decode('utf-8')

            cookies = {}
            for cookie in cookie_header.split(';'):
                if '=' in cookie:
                    key, value = cookie.strip().split('=', 1)
                    cookies[key] = value


            jwt_token = cookies.get(settings.SIMPLE_JWT['AUTH_COOKIE'])
            
            if jwt_token:
                scope['user'] = await get_user_from_token(jwt_token)
            else:
                scope['user'] = AnonymousUser() 
        
        return await self.app(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
