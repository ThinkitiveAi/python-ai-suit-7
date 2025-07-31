from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db, get_provider_collection
from app.schemas.provider_schema import (
    ProviderRegistrationRequest,
    ProviderRegistrationResponse,
    ErrorResponse,
    ProviderDetailResponse,
)
from app.services.provider_service import ProviderService
from app.utils.email_utils import verify_token
from app.core.database import VerificationStatus
from loguru import logger


router = APIRouter(prefix="/api/v1/provider", tags=["Provider Registration"])


@router.post(
    "/register",
    response_model=ProviderRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_provider(
    request: Request,
    provider_data: ProviderRegistrationRequest,
    db: Session = Depends(get_db),
):
    """
    Register a new healthcare provider.

    This endpoint handles provider registration with comprehensive validation,
    secure password hashing, and email verification.

    Args:
        request (Request): FastAPI request object
        provider_data (ProviderRegistrationRequest): Provider registration data
        db (Session): Database session

    Returns:
        ProviderRegistrationResponse: Registration response with provider details

    Raises:
        HTTPException: For validation errors, duplicate data, or server errors
    """
    try:
        # Get sanitized data from middleware if available
        sanitized_data = getattr(request.state, "sanitized_data", None)

        if sanitized_data:
            # Use sanitized data from middleware
            registration_data = sanitized_data
        else:
            # Fallback to original data (for testing or if middleware is disabled)
            registration_data = provider_data.dict()

        # Initialize provider service
        mongo_collection = get_provider_collection()
        provider_service = ProviderService(db, mongo_collection)

        # Register provider
        success, response_data, error_message = provider_service.register_provider(
            registration_data
        )

        if not success:
            # Handle validation errors
            if "errors" in response_data:
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content=response_data,
                )

            # Handle duplicate data
            if "already registered" in error_message.lower():
                return JSONResponse(
                    status_code=status.HTTP_409_CONFLICT, content=response_data
                )

            # Handle other errors
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response_data
            )

        # Log successful registration
        logger.info(
            f"Provider registration successful: {response_data['data']['provider_id']}"
        )

        return JSONResponse(status_code=status.HTTP_201_CREATED, content=response_data)

    except Exception as e:
        logger.error(f"Unexpected error in provider registration: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Internal server error",
                "error": "INTERNAL_ERROR",
            },
        )


@router.get("/verify", response_model=Dict[str, Any])
async def verify_provider_email(token: str, db: Session = Depends(get_db)):
    """
    Verify provider email address using verification token.

    Args:
        token (str): Verification token from email
        db (Session): Database session

    Returns:
        Dict[str, Any]: Verification response
    """
    try:
        # Verify token
        payload = verify_token(token)

        if not payload:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "Invalid or expired verification token",
                    "error": "INVALID_TOKEN",
                },
            )

        # Check token type
        if payload.get("type") != "email_verification":
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "Invalid token type",
                    "error": "INVALID_TOKEN_TYPE",
                },
            )

        provider_id = payload.get("provider_id")
        email = payload.get("email")

        if not provider_id or not email:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "Invalid token payload",
                    "error": "INVALID_TOKEN_PAYLOAD",
                },
            )

        # Initialize provider service
        mongo_collection = get_provider_collection()
        provider_service = ProviderService(db, mongo_collection)

        # Get provider details
        provider = provider_service.get_provider_by_id(provider_id)

        if not provider:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "success": False,
                    "message": "Provider not found",
                    "error": "PROVIDER_NOT_FOUND",
                },
            )

        # Check if email matches
        if provider.get("email") != email:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "success": False,
                    "message": "Email mismatch",
                    "error": "EMAIL_MISMATCH",
                },
            )

        # Check if already verified
        if provider.get("verification_status") == VerificationStatus.VERIFIED.value:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": "Email already verified",
                    "data": {
                        "provider_id": provider_id,
                        "email": email,
                        "verification_status": VerificationStatus.VERIFIED.value,
                    },
                },
            )

        # Update verification status
        update_success = provider_service.update_verification_status(
            provider_id, VerificationStatus.VERIFIED
        )

        if not update_success:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "message": "Failed to update verification status",
                    "error": "UPDATE_FAILED",
                },
            )

        # Send welcome email
        from app.services.email_service import EmailService

        email_service = EmailService()
        email_service.send_welcome_email(
            email=email,
            first_name=provider.get("first_name", ""),
            last_name=provider.get("last_name", ""),
        )

        logger.info(f"Provider email verified successfully: {provider_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Email verified successfully. Welcome!",
                "data": {
                    "provider_id": provider_id,
                    "email": email,
                    "verification_status": VerificationStatus.VERIFIED.value,
                },
            },
        )

    except Exception as e:
        logger.error(f"Error in email verification: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Internal server error during verification",
                "error": "VERIFICATION_ERROR",
            },
        )


@router.get("/{provider_id}", response_model=ProviderDetailResponse)
async def get_provider_details(provider_id: str, db: Session = Depends(get_db)):
    """
    Get provider details by ID.

    Args:
        provider_id (str): Provider's unique ID
        db (Session): Database session

    Returns:
        ProviderDetailResponse: Provider details
    """
    try:
        # Initialize provider service
        mongo_collection = get_provider_collection()
        provider_service = ProviderService(db, mongo_collection)

        # Get provider details
        provider = provider_service.get_provider_by_id(provider_id)

        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
            )

        return provider

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting provider details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """
    Health check endpoint.

    Returns:
        Dict[str, Any]: Health status
    """
    return {
        "status": "healthy",
        "service": "Provider Registration API",
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z",
    }
