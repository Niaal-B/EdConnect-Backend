from auth.views import (CheckSessionView, CookieTokenRefreshView,
                        ForgotPasswordView, ResetPasswordView, VerifyAuthView)
from django.urls import path

urlpatterns = [
    path('verify',VerifyAuthView.as_view(),name='verify-auth'),
    path('check-session',CheckSessionView.as_view(),name='check-session'),
    path('token/refresh', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/<uidb64>/<token>/', ResetPasswordView.as_view(), name='reset-password'),

    
]
