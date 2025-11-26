from celery import shared_task
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings

User = get_user_model()


@shared_task
def send_verification_email(user_id):
    """Send email verification link to user"""
    try:
        user = User.objects.get(pk=user_id)
        
        # Generate verification token with UUID as string
        uid = urlsafe_base64_encode(force_bytes(str(user.pk)))
        token = default_token_generator.make_token(user)
        verification_link = f"{settings.FRONTEND_URL}/verify-email/{uid}:{token}"
        
        subject = 'Verify Your Email - Audioverse'
        message = f"""
        Hi {user.username},
        
        Thank you for registering with Audioverse!
        
        Please click the link below to verify your email address:
        {verification_link}

        Degug:
            - uid: {uid}
            - token: {token}
        
        This link will expire in 24 hours.
        
        If you didn't create this account, please ignore this email.
        
        Best regards,
        The Audioverse Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        return f"Verification email sent to {user.email}"
    except User.DoesNotExist:
        return f"User with id {user_id} not found"
    except Exception as e:
        return f"Error sending verification email: {str(e)}"


@shared_task
def send_welcome_email(user_id):
    """Send welcome email after successful verification"""
    try:
        user = User.objects.get(pk=user_id)
        
        subject = 'Welcome to Audioverse!'
        message = f"""
        Hi {user.username},
        
        Welcome to Audioverse! 🎧
        
        Your email has been successfully verified. You can now enjoy:
        
        • Access to thousands of audiobooks
        • Personalized recommendations
        • Track your listening progress
        • Create favorites and playlists
        • Write reviews and ratings
        
        Start exploring our collection today!
        
        Happy listening,
        The Audioverse Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        return f"Welcome email sent to {user.email}"
    except User.DoesNotExist:
        return f"User with id {user_id} not found"
    except Exception as e:
        return f"Error sending welcome email: {str(e)}"


@shared_task
def send_password_reset_email(user_id):
    """Send password reset link to user"""
    try:
        user = User.objects.get(pk=user_id)
        
        # Generate reset token with UUID as string
        uid = urlsafe_base64_encode(force_bytes(str(user.pk)))
        token = default_token_generator.make_token(user)
        reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}:{token}"
        
        subject = 'Password Reset Request - Audioverse'
        message = f"""
        Hi {user.username},
        
        We received a request to reset your password for your Audioverse account.
        
        Click the link below to reset your password:
        {reset_link}

        Debug:
            - uid: {uid}
            - Token: {token}
        
        This link will expire in 24 hours.
        
        If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
        
        Best regards,
        The Audioverse Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        return f"Password reset email sent to {user.email}"
    except User.DoesNotExist:
        return f"User with id {user_id} not found"
    except Exception as e:
        return f"Error sending password reset email: {str(e)}"