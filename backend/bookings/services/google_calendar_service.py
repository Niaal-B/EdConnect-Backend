import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from django.conf import settings
from django.utils import timezone
import logging

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

logger = logging.getLogger(__name__) 

def get_google_calendar_service(user_google_tokens):
    if not user_google_tokens:
        logger.error("UserGoogleTokens object is None. Cannot get Google Calendar service. "
                     "This likely means the user has not connected their Google Calendar or their token record is missing.")
        return None

    is_expired = user_google_tokens.is_access_token_expired()

    creds = Credentials(
        token=user_google_tokens.access_token,
        refresh_token=user_google_tokens.refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=SCOPES,
        expiry=user_google_tokens.expires_in
    )

    if is_expired and creds.refresh_token:
        logger.info(f"Token for {user_google_tokens.user.email} is expired or nearing expiry. Attempting to refresh...")
        try:
            creds.refresh(Request())
            user_google_tokens.access_token = creds.token
            user_google_tokens.expires_in = creds.expiry
            user_google_tokens.scope = ' '.join(creds.scopes) if creds.scopes else user_google_tokens.scope
            user_google_tokens.save(update_fields=['access_token', 'expires_in', 'scope', 'updated_at'])
            logger.info(f"SUCCESS: Google access token refreshed for user {user_google_tokens.user.email}.")
        except Exception as e:
            logger.error(f"ERROR: Failed to refresh Google access token for user {user_google_tokens.user.email}: {e}")
            return None
    elif not creds.refresh_token:
        logger.warning(f"No refresh token available for user {user_google_tokens.user.email}. User needs to re-authenticate for continued access.")
        return None
    elif not creds.valid:
        logger.error(f"Google credentials are not valid for user {user_google_tokens.user.email}. User needs to re-authenticate.")
        return None

    try:
        service = build('calendar', 'v3', credentials=creds)
        logger.info(f"SUCCESS: Google Calendar service object built for user {user_google_tokens.user.email}.")
        return service
    except Exception as e:
        logger.error(f"ERROR: Failed to build Google Calendar service for user {user_google_tokens.user.email}: {e}")
        return None
