from typing import Optional
from datetime import datetime
from app.utils.email_utils import (
    send_verification_email,
    send_welcome_email,
    generate_verification_token,
)
from app.core.config import settings
from loguru import logger


class EmailService:
    """Service for handling email operations."""

    def __init__(self):
        self.smtp_configured = bool(settings.smtp_username and settings.smtp_password)

    def send_provider_verification_email(
        self, provider_id: str, email: str, first_name: str, last_name: str
    ) -> bool:
        """
        Send verification email to newly registered provider.

        Args:
            provider_id (str): Provider's unique ID
            email (str): Provider's email address
            first_name (str): Provider's first name
            last_name (str): Provider's last name

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Generate verification token
            verification_token = generate_verification_token(provider_id, email)

            # Prepare provider name
            provider_name = f"{first_name} {last_name}"

            # Send verification email
            success = send_verification_email(email, provider_name, verification_token)

            if success:
                logger.info(
                    f"Verification email sent successfully to {email} for provider {provider_id}"
                )
            else:
                logger.warning(
                    f"Failed to send verification email to {email} for provider {provider_id}"
                )

            return success

        except Exception as e:
            logger.error(f"Error sending verification email to {email}: {e}")
            return False

    def send_welcome_email(self, email: str, first_name: str, last_name: str) -> bool:
        """
        Send welcome email after successful verification.

        Args:
            email (str): Provider's email address
            first_name (str): Provider's first name
            last_name (str): Provider's last name

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            provider_name = f"{first_name} {last_name}"
            success = send_welcome_email(email, provider_name)

            if success:
                logger.info(f"Welcome email sent successfully to {email}")
            else:
                logger.warning(f"Failed to send welcome email to {email}")

            return success

        except Exception as e:
            logger.error(f"Error sending welcome email to {email}: {e}")
            return False

    def is_email_service_available(self) -> bool:
        """
        Check if email service is properly configured.

        Returns:
            bool: True if email service is available, False otherwise
        """
        return self.smtp_configured

    def log_email_attempt(
        self,
        email: str,
        email_type: str,
        success: bool,
        provider_id: Optional[str] = None,
    ):
        """
        Log email sending attempts for audit purposes.

        Args:
            email (str): Recipient email address
            email_type (str): Type of email (verification, welcome, etc.)
            success (bool): Whether email was sent successfully
            provider_id (Optional[str]): Provider ID if applicable
        """
        timestamp = datetime.utcnow().isoformat()
        status = "SUCCESS" if success else "FAILED"

        log_entry = {
            "timestamp": timestamp,
            "email": email,
            "email_type": email_type,
            "status": status,
            "provider_id": provider_id,
            "smtp_configured": self.smtp_configured,
        }

        if success:
            logger.info(f"Email {email_type} sent successfully to {email}")
        else:
            logger.error(f"Email {email_type} failed to send to {email}")

        # In a production environment, you might want to store this in a database
        # for audit purposes
        return log_entry
