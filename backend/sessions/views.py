import os
import time

from agora_token_builder import RtcTokenBuilder
from auth.authentication import CookieJWTAuthentication
from django.conf import settings
from dotenv import load_dotenv
from rest_framework.decorators import (api_view, authentication_classes,
                                       permission_classes)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

AGORA_APP_ID =os.environ.get('AGORA_APP_ID')

AGORA_APP_CERTIFICATE = os.environ.get('AGORA_APP_CERTIFICATE')

@api_view(['POST'])
@authentication_classes([CookieJWTAuthentication]) 
@permission_classes([IsAuthenticated])
def get_agora_token(request):
    user = request.user
    channel_name = request.data.get('channelName')

    if not channel_name:
        return Response({'error': 'Channel name is required.'}, status=400)

    token_expire_time = 3600 * 2

    # We'll use the user's ID as their unique ID in the Agora channel
    uid = int(user.id)
    role = 1 # 1 for host, 2 for audience. For a call, everyone is a host.

    current_time_stamp = int(time.time())
    privilege_expire_time = current_time_stamp + token_expire_time

    # Build the token with the credentials and user info
    token = RtcTokenBuilder.buildTokenWithUid(
        AGORA_APP_ID, 
        AGORA_APP_CERTIFICATE, 
        channel_name, 
        uid, 
        role, 
        privilege_expire_time
    )

    return Response({'token': token, 'appId': AGORA_APP_ID, 'uid': uid,})