from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_verification_email(email, token):
    verification_url = f"http://localhost:3000/verify-email/{token}/"
    
    send_mail(
        subject="Verify Your EdConnect Account",
        message=f"Click to verify: {verification_url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )