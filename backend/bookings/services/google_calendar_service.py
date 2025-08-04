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


def _build_event_body(booking, user_type_info=""):
    start_time_iso = booking.booked_start_time.isoformat()
    end_time_iso = booking.booked_end_time.isoformat()

    timezone_name = booking.booked_start_time.tzinfo.tzname(booking.booked_start_time) \
                    if booking.booked_start_time.tzinfo else settings.TIME_ZONE

    summary_prefix = f"Mentorship Session ({user_type_info})" if user_type_info else "Mentorship Session"
    summary = f"{summary_prefix} - {booking.student.username} with {booking.mentor.username}"

    description_lines = [
        f"Booking ID: {booking.id}",
        f"Mentor: {booking.mentor.username}",
        f"Student: {booking.student.username}",
        f"Status: {booking.status}",
        f"View/Join Session: {settings.FRONTEND_URL}/dashboard/sessions/{booking.id}"
    ]
    description = '\n'.join(description_lines)

    attendees = [
        {'email': booking.mentor.email, 'displayName': booking.mentor.username},
        {'email': booking.student.email, 'displayName': booking.student.username},
    ]

    reminders = {
        'useDefault': False,
        'overrides': [
            {'method': 'email', 'minutes': 24 * 60},
            {'method': 'popup', 'minutes': 10},
        ],
    }

    conference_data = {
        'createRequest': {
            'requestId': f"mentorship-{booking.id}-{datetime.datetime.now().timestamp()}",
            'conferenceSolutionKey': {'type': 'hangoutsMeet'}
        },
        'parameters': {
            'addOnAvailable': True
        }
    }

    event_body = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time_iso,
            'timeZone': timezone_name
        },
        'end': {
            'dateTime': end_time_iso,
            'timeZone': timezone_name
        },
        'attendees': attendees,
        'reminders': reminders,
        'conferenceData': conference_data,
    }

    return event_body