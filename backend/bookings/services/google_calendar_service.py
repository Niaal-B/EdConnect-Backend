import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from django.conf import settings
from django.utils import timezone


SCOPES = ['https://www.googleapis.com/auth/calendar.events']


