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



@shared_task
def send_reset_password_email(email, reset_link):
    subject = "Reset Your Password"
    message = f"Click the link to reset your password: {reset_link}"
    from_email = "no-reply@example.com"

    send_mail(
        subject,
        message,
        from_email,
        [email],
        fail_silently=False
    )
