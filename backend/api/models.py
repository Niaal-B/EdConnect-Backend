from django.conf import settings
from django.db import models


class UserGoogleTokens(models.Model):
    """
    Stores Google's OAuth 2.0 access and refresh tokens for each Django user.
    This allows the Django backend to make API calls to Google services
    (like Calendar) on behalf of the user, even when they are offline.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='google_tokens', 
        verbose_name="Django User"
    )

    access_token = models.CharField(max_length=255, verbose_name="Google Access Token")
    refresh_token = models.CharField(max_length=255, null=True, blank=True, verbose_name="Google Refresh Token")
    expires_in = models.DateTimeField(verbose_name="Access Token Expiry Time") 
    token_type = models.CharField(max_length=50, default='Bearer', verbose_name="Token Type") 

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Updated At")

    def is_access_token_expired(self):
        return self.expires_in <= timezone.now() + timezone.timedelta(minutes=5)


    class Meta:
        verbose_name = "User Google Token"
        verbose_name_plural = "User Google Tokens"

    def __str__(self):
        return f"Tokens for {self.user.email}"