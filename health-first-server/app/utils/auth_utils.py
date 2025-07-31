import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from loguru import logger

from app.core.config import settings
from app.services.patient_service import PatientService

# Security
security = HTTPBearer()

# Initialize service
patient_service = PatientService()


def verify_patient_token(token: str) -> Optional[str]:
    """
    Verify JWT token and return patient ID if valid.

    Args:
        token: JWT token string

    Returns:
        Patient ID if token is valid, None otherwise

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Decode token
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )

        # Check token role
        if payload.get("role") != "patient":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Invalid token role",
                    "error_code": "INVALID_TOKEN_ROLE",
                },
            )

        # Get patient ID
        patient_id = payload.get("patient_id")
        if not patient_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Token missing patient ID",
                    "error_code": "INVALID_TOKEN",
                },
            )

        return patient_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Token has expired",
                "error_code": "TOKEN_EXPIRED",
            },
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Invalid token",
                "error_code": "INVALID_TOKEN",
            },
        )
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Token verification failed",
                "error_code": "TOKEN_VERIFICATION_FAILED",
            },
        )


async def get_current_patient_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Get current patient ID from JWT token.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        Patient ID from token

    Raises:
        HTTPException: If token is invalid or patient not found
    """
    try:
        # Verify token
        patient_id = verify_patient_token(credentials.credentials)

        # Verify patient exists and is active
        result = patient_service.get_patient_profile(patient_id)
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Patient not found or inactive",
                    "error_code": "PATIENT_NOT_FOUND",
                },
            )

        return patient_id

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current patient ID: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Authentication failed",
                "error_code": "AUTHENTICATION_FAILED",
            },
        )


def verify_refresh_token(refresh_token: str) -> Optional[str]:
    """
    Verify refresh token and return patient ID if valid.

    Args:
        refresh_token: JWT refresh token string

    Returns:
        Patient ID if token is valid, None otherwise

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Decode token
        payload = jwt.decode(
            refresh_token, settings.secret_key, algorithms=[settings.algorithm]
        )

        # Check token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Invalid token type",
                    "error_code": "INVALID_TOKEN_TYPE",
                },
            )

        # Get patient ID
        patient_id = payload.get("patient_id")
        if not patient_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Token missing patient ID",
                    "error_code": "INVALID_TOKEN",
                },
            )

        return patient_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Refresh token has expired",
                "error_code": "TOKEN_EXPIRED",
            },
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Invalid refresh token",
                "error_code": "INVALID_TOKEN",
            },
        )
    except Exception as e:
        logger.error(f"Error verifying refresh token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Refresh token verification failed",
                "error_code": "TOKEN_VERIFICATION_FAILED",
            },
        )


def create_access_token(patient_id: str, email: str) -> str:
    """
    Create a new access token for a patient.

    Args:
        patient_id: Patient ID
        email: Patient's email

    Returns:
        JWT access token
    """
    from datetime import datetime, timedelta

    # Access token (30 minutes as per user story)
    access_token_expires = datetime.utcnow() + timedelta(minutes=30)
    access_token_data = {
        "patient_id": patient_id,
        "email": email,
        "role": "patient",
        "exp": access_token_expires,
        "iat": datetime.utcnow(),
    }

    return jwt.encode(
        access_token_data, settings.secret_key, algorithm=settings.algorithm
    )


def create_refresh_token(patient_id: str, email: str) -> str:
    """
    Create a new refresh token for a patient.

    Args:
        patient_id: Patient ID
        email: Patient's email

    Returns:
        JWT refresh token
    """
    from datetime import datetime, timedelta

    # Refresh token (long-lived)
    refresh_token_expires = datetime.utcnow() + timedelta(days=30)
    refresh_token_data = {
        "patient_id": patient_id,
        "email": email,
        "role": "patient",
        "type": "refresh",
        "exp": refresh_token_expires,
        "iat": datetime.utcnow(),
    }

    return jwt.encode(
        refresh_token_data, settings.secret_key, algorithm=settings.algorithm
    )
