from django.urls import path
from auth.views import VerifyAuthView,CheckSessionView,CookieTokenRefreshView

urlpatterns = [
    path('verify',VerifyAuthView.as_view(),name='verify-auth'),
    path('check-session',CheckSessionView.as_view(),name='check-session'),
    path('token/refresh', CookieTokenRefreshView.as_view(), name='token_refresh')
    
]
