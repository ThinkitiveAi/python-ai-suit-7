import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from loguru import logger

from app.core.config import settings


def send_verification_email(email: str, patient_id: str) -> bool:
    """
    Send verification email to patient.

    Args:
        email: Patient's email address
        patient_id: Patient's unique ID

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Check if email settings are configured
        if not all(
            [settings.smtp_server, settings.smtp_username, settings.smtp_password]
        ):
            logger.warning("Email settings not configured, skipping email verification")
            return False

        # Create message
        msg = MIMEMultipart()
        msg["From"] = settings.email_from
        msg["To"] = email
        msg["Subject"] = "Verify Your Patient Account"

        # Create verification link
        verification_link = f"https://your-domain.com/verify-email?token={patient_id}"

        # Email body
        body = f"""
        <html>
        <body>
            <h2>Welcome to Health First!</h2>
            <p>Thank you for registering as a patient. To complete your registration, please verify your email address by clicking the link below:</p>
            
            <p><a href="{verification_link}" style="background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px;">Verify Email Address</a></p>
            
            <p>Or copy and paste this link into your browser:</p>
            <p>{verification_link}</p>
            
            <p>This link will expire in 24 hours.</p>
            
            <p>If you did not create an account, please ignore this email.</p>
            
            <p>Best regards,<br>The Health First Team</p>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, "html"))

        # Send email
        server = smtplib.SMTP(settings.smtp_server, settings.smtp_port)
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        text = msg.as_string()
        server.sendmail(settings.email_from, email, text)
        server.quit()

        logger.info(f"Verification email sent to {email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {e}")
        return False


def send_password_reset_email(email: str, reset_token: str) -> bool:
    """
    Send password reset email to patient.

    Args:
        email: Patient's email address
        reset_token: Password reset token

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Check if email settings are configured
        if not all(
            [settings.smtp_server, settings.smtp_username, settings.smtp_password]
        ):
            logger.warning(
                "Email settings not configured, skipping password reset email"
            )
            return False

        # Create message
        msg = MIMEMultipart()
        msg["From"] = settings.email_from
        msg["To"] = email
        msg["Subject"] = "Reset Your Password"

        # Create reset link
        reset_link = f"https://your-domain.com/reset-password?token={reset_token}"

        # Email body
        body = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You have requested to reset your password. Click the link below to create a new password:</p>
            
            <p><a href="{reset_link}" style="background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px;">Reset Password</a></p>
            
            <p>Or copy and paste this link into your browser:</p>
            <p>{reset_link}</p>
            
            <p>This link will expire in 1 hour.</p>
            
            <p>If you did not request a password reset, please ignore this email.</p>
            
            <p>Best regards,<br>The Health First Team</p>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, "html"))

        # Send email
        server = smtplib.SMTP(settings.smtp_server, settings.smtp_port)
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        text = msg.as_string()
        server.sendmail(settings.email_from, email, text)
        server.quit()

        logger.info(f"Password reset email sent to {email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send password reset email to {email}: {e}")
        return False


def send_welcome_email(email: str, first_name: str) -> bool:
    """
    Send welcome email to newly registered patient.

    Args:
        email: Patient's email address
        first_name: Patient's first name

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Check if email settings are configured
        if not all(
            [settings.smtp_server, settings.smtp_username, settings.smtp_password]
        ):
            logger.warning("Email settings not configured, skipping welcome email")
            return False

        # Create message
        msg = MIMEMultipart()
        msg["From"] = settings.email_from
        msg["To"] = email
        msg["Subject"] = "Welcome to Health First!"

        # Email body
        body = f"""
        <html>
        <body>
            <h2>Welcome to Health First, {first_name}!</h2>
            <p>Thank you for joining our healthcare platform. We're excited to have you as part of our community.</p>
            
            <h3>What you can do now:</h3>
            <ul>
                <li>Complete your profile with additional information</li>
                <li>Browse available healthcare providers</li>
                <li>Schedule appointments</li>
                <li>Access your medical records</li>
            </ul>
            
            <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
            
            <p>Best regards,<br>The Health First Team</p>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, "html"))

        # Send email
        server = smtplib.SMTP(settings.smtp_server, settings.smtp_port)
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        text = msg.as_string()
        server.sendmail(settings.email_from, email, text)
        server.quit()

        logger.info(f"Welcome email sent to {email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send welcome email to {email}: {e}")
        return False
