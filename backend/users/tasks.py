from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail


@shared_task
def send_verification_email(email, token):
    verification_url = f"{settings.FRONTEND_URL}/verify-email/{token}/"

    subject = "Verify Your EdConnect Account"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [email]

    text_content = f"Verify your email: {verification_url}"

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color:#2563eb;">Welcome to EdConnect!</h2>
        <p>Thank you for signing up. Please verify your email by clicking the button below:</p>
        <a href="{verification_url}" style="display:inline-block;background-color:#2563eb;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;">Verify Email</a>
        <p style="margin-top:20px;">If the button doesn’t work, use this link:</p>
        <p>{verification_url}</p>
      </body>
    </html>
    """

    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()

@shared_task
def send_reset_password_email(email, reset_link):
    subject = "Reset Your EdConnect Password"
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [email]

    text_content = f"Reset your password here: {reset_link}"

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color:#dc2626;">Reset Your Password</h2>
        <p>Click the button below to reset your password:</p>
        <a href="{reset_link}" style="display:inline-block;background-color:#dc2626;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;">Reset Password</a>
        <p style="margin-top:20px;">If the button doesn’t work, copy and paste this link into your browser:</p>
        <p>{reset_link}</p>
      </body>
    </html>
    """

    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()