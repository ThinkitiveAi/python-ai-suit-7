import re
import html
from typing import Any, Dict
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger


class InputSanitizer:
    """Input sanitization utilities."""

    @staticmethod
    def sanitize_string(value: str) -> str:
        """
        Sanitize a string value to prevent injection attacks.

        Args:
            value (str): Input string to sanitize

        Returns:
            str: Sanitized string
        """
        if not isinstance(value, str):
            return str(value)

        # Remove null bytes
        value = value.replace("\x00", "")

        # HTML escape to prevent XSS
        value = html.escape(value)

        # Remove potentially dangerous characters
        dangerous_chars = [
            "<script>",
            "</script>",
            "javascript:",
            "vbscript:",
            "onload=",
            "onerror=",
        ]
        for char in dangerous_chars:
            value = value.replace(char.lower(), "")
            value = value.replace(char.upper(), "")

        # Trim whitespace
        value = value.strip()

        return value

    @staticmethod
    def sanitize_email(email: str) -> str:
        """
        Sanitize email address.

        Args:
            email (str): Email address to sanitize

        Returns:
            str: Sanitized email address
        """
        if not email:
            return ""

        # Convert to lowercase and trim
        email = email.lower().strip()

        # Remove any HTML tags
        email = re.sub(r"<[^>]+>", "", email)

        # Remove null bytes
        email = email.replace("\x00", "")

        return email

    @staticmethod
    def sanitize_phone(phone: str) -> str:
        """
        Sanitize phone number.

        Args:
            phone (str): Phone number to sanitize

        Returns:
            str: Sanitized phone number
        """
        if not phone:
            return ""

        # Remove all non-digit characters except + and -
        phone = re.sub(r"[^\d+\-\(\)\s]", "", phone)

        # Remove null bytes
        phone = phone.replace("\x00", "")

        return phone.strip()

    @staticmethod
    def sanitize_license_number(license_num: str) -> str:
        """
        Sanitize license number.

        Args:
            license_num (str): License number to sanitize

        Returns:
            str: Sanitized license number
        """
        if not license_num:
            return ""

        # Remove all non-alphanumeric characters
        license_num = re.sub(r"[^a-zA-Z0-9]", "", license_num)

        # Convert to uppercase
        license_num = license_num.upper()

        return license_num


class ValidationMiddleware:
    """Middleware for input validation and sanitization."""

    def __init__(self):
        self.sanitizer = InputSanitizer()

    def sanitize_provider_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize provider registration data.

        Args:
            data (Dict[str, Any]): Raw provider data

        Returns:
            Dict[str, Any]: Sanitized provider data
        """
        sanitized_data = {}

        # Sanitize basic fields
        if "first_name" in data:
            sanitized_data["first_name"] = self.sanitizer.sanitize_string(
                data["first_name"]
            )

        if "last_name" in data:
            sanitized_data["last_name"] = self.sanitizer.sanitize_string(
                data["last_name"]
            )

        if "email" in data:
            sanitized_data["email"] = self.sanitizer.sanitize_email(data["email"])

        if "phone_number" in data:
            sanitized_data["phone_number"] = self.sanitizer.sanitize_phone(
                data["phone_number"]
            )

        if "password" in data:
            # Don't sanitize password as it might contain special characters
            sanitized_data["password"] = data["password"]

        if "confirm_password" in data:
            # Don't sanitize password confirmation
            sanitized_data["confirm_password"] = data["confirm_password"]

        if "specialization" in data:
            sanitized_data["specialization"] = self.sanitizer.sanitize_string(
                data["specialization"]
            )

        if "license_number" in data:
            sanitized_data["license_number"] = self.sanitizer.sanitize_license_number(
                data["license_number"]
            )

        if "years_of_experience" in data:
            try:
                sanitized_data["years_of_experience"] = int(data["years_of_experience"])
            except (ValueError, TypeError):
                sanitized_data["years_of_experience"] = 0

        # Sanitize clinic address
        if "clinic_address" in data and isinstance(data["clinic_address"], dict):
            clinic_address = data["clinic_address"]
            sanitized_data["clinic_address"] = {
                "street": self.sanitizer.sanitize_string(
                    clinic_address.get("street", "")
                ),
                "city": self.sanitizer.sanitize_string(clinic_address.get("city", "")),
                "state": self.sanitizer.sanitize_string(
                    clinic_address.get("state", "")
                ),
                "zip": self.sanitizer.sanitize_string(clinic_address.get("zip", "")),
            }

        return sanitized_data

    def validate_content_type(self, request: Request) -> bool:
        """
        Validate that the request has the correct content type.

        Args:
            request (Request): FastAPI request object

        Returns:
            bool: True if content type is valid, False otherwise
        """
        content_type = request.headers.get("content-type", "")
        return "application/json" in content_type.lower()

    def validate_request_size(self, request: Request) -> bool:
        """
        Validate that the request body is not too large.

        Args:
            request (Request): FastAPI request object

        Returns:
            bool: True if request size is acceptable, False otherwise
        """
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                max_size = 1024 * 1024  # 1MB
                return size <= max_size
            except ValueError:
                return False
        return True


# Global validation middleware instance
validation_middleware = ValidationMiddleware()


async def validation_middleware_handler(request: Request, call_next):
    """
    Validation middleware handler for FastAPI.

    Args:
        request (Request): FastAPI request object
        call_next: Next middleware/endpoint function

    Returns:
        Response: FastAPI response
    """
    # Only apply validation to registration endpoint
    if request.url.path == "/api/v1/provider/register" and request.method == "POST":
        try:
            # Validate content type
            if not validation_middleware.validate_content_type(request):
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "message": "Invalid content type. Expected application/json",
                        "error": "INVALID_CONTENT_TYPE",
                    },
                )

            # Validate request size
            if not validation_middleware.validate_request_size(request):
                return JSONResponse(
                    status_code=413,
                    content={
                        "success": False,
                        "message": "Request body too large",
                        "error": "REQUEST_TOO_LARGE",
                    },
                )

            # Get request body
            body = await request.body()

            # Store sanitized data in request state for later use
            if body:
                import json

                try:
                    raw_data = json.loads(body.decode("utf-8"))
                    sanitized_data = validation_middleware.sanitize_provider_data(
                        raw_data
                    )
                    request.state.sanitized_data = sanitized_data
                except json.JSONDecodeError:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "success": False,
                            "message": "Invalid JSON format",
                            "error": "INVALID_JSON",
                        },
                    )

            # Continue to next middleware/endpoint
            response = await call_next(request)
            return response

        except Exception as e:
            logger.error(f"Validation middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Internal server error during validation",
                    "error": "VALIDATION_ERROR",
                },
            )

    # For non-registration endpoints, just pass through
    return await call_next(request)
