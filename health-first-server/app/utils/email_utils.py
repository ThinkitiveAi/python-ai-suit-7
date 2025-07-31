import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import secrets
import string
from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings
from loguru import logger


def generate_verification_token(provider_id: str, email: str) -> str:
    """
    Generate a JWT token for email verification.

    Args:
        provider_id (str): Provider's unique ID
        email (str): Provider's email address

    Returns:
        str: JWT verification token
    """
    payload = {
        "provider_id": provider_id,
        "email": email,
        "type": "email_verification",
        "exp": datetime.utcnow() + timedelta(hours=24),  # Token expires in 24 hours
    }

    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.

    Args:
        token (str): JWT token to verify

    Returns:
        Optional[dict]: Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        return None


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a secure random token.

    Args:
        length (int): Length of the token

    Returns:
        str: Secure random token
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def send_verification_email(
    email: str, provider_name: str, verification_token: str
) -> bool:
    """
    Send verification email to the provider.

    Args:
        email (str): Recipient email address
        provider_name (str): Provider's full name
        verification_token (str): Verification token

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not settings.smtp_username or not settings.smtp_password:
        logger.warning("SMTP credentials not configured. Skipping email send.")
        return False

    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Verify Your Provider Registration"
        message["From"] = settings.email_from
        message["To"] = email

        # Create verification URL
        verification_url = (
            f"http://localhost:8000/api/v1/provider/verify?token={verification_token}"
        )

        # HTML content
        html_content = f"""
        <html>
        <body>
            <h2>Welcome to Provider Registration!</h2>
            <p>Dear {provider_name},</p>
            <p>Thank you for registering as a healthcare provider. To complete your registration, please click the link below to verify your email address:</p>
            <p><a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px;">Verify Email Address</a></p>
            <p>Or copy and paste this link into your browser:</p>
            <p>{verification_url}</p>
            <p>This link will expire in 24 hours.</p>
            <p>If you did not register for this account, please ignore this email.</p>
            <p>Best regards,<br>Provider Registration Team</p>
        </body>
        </html>
        """

        # Plain text content
        text_content = f"""
        Welcome to Provider Registration!
        
        Dear {provider_name},
        
        Thank you for registering as a healthcare provider. To complete your registration, please visit the following link to verify your email address:
        
        {verification_url}
        
        This link will expire in 24 hours.
        
        If you did not register for this account, please ignore this email.
        
        Best regards,
        Provider Registration Team
        """

        # Attach content
        text_part = MIMEText(text_content, "plain")
        html_part = MIMEText(html_content, "html")
        message.attach(text_part)
        message.attach(html_part)

        # Send email
        context = ssl.create_default_context()
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.starttls(context=context)
            server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.email_from, email, message.as_string())

        logger.info(f"Verification email sent successfully to {email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {e}")
        return False


def send_welcome_email(email: str, provider_name: str) -> bool:
    """
    Send welcome email after successful verification.

    Args:
        email (str): Recipient email address
        provider_name (str): Provider's full name

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not settings.smtp_username or not settings.smtp_password:
        logger.warning("SMTP credentials not configured. Skipping email send.")
        return False

    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Welcome! Your Provider Account is Verified"
        message["From"] = settings.email_from
        message["To"] = email

        # HTML content
        html_content = f"""
        <html>
        <body>
            <h2>Welcome to Provider Registration!</h2>
            <p>Dear {provider_name},</p>
            <p>Congratulations! Your provider account has been successfully verified. You can now access your account and start using our platform.</p>
            <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
            <p>Best regards,<br>Provider Registration Team</p>
        </body>
        </html>
        """

        # Plain text content
        text_content = f"""
        Welcome to Provider Registration!
        
        Dear {provider_name},
        
        Congratulations! Your provider account has been successfully verified. You can now access your account and start using our platform.
        
        If you have any questions or need assistance, please don't hesitate to contact our support team.
        
        Best regards,
        Provider Registration Team
        """

        # Attach content
        text_part = MIMEText(text_content, "plain")
        html_part = MIMEText(html_content, "html")
        message.attach(text_part)
        message.attach(html_part)

        # Send email
        context = ssl.create_default_context()
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.starttls(context=context)
            server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.email_from, email, message.as_string())

        logger.info(f"Welcome email sent successfully to {email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send welcome email to {email}: {e}")
        return False
