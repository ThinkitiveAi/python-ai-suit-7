from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from loguru import logger

from app.services.patient_service import PatientService
from app.schemas.patient_schema import (
    PatientRegistrationRequest,
    PatientRegistrationResponse,
    PatientLoginRequest,
    PatientLoginResponse,
    PatientUpdateRequest,
    PatientDetailResponse,
    ErrorResponse,
    ValidationErrorResponse,
)
from app.utils.auth_utils import verify_patient_token, get_current_patient_id

# Create router
router = APIRouter(prefix="/api/v1/patient", tags=["Patient"])

# Security
security = HTTPBearer()

# Initialize service
patient_service = PatientService()


@router.post(
    "/register",
    response_model=PatientRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Patient registered successfully"},
        422: {"model": ValidationErrorResponse, "description": "Validation failed"},
        409: {"model": ErrorResponse, "description": "Email or phone already exists"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def register_patient(patient_data: PatientRegistrationRequest):
    """
    Register a new patient with comprehensive validation and security features.

    - **first_name**: Patient's first name (2-50 characters)
    - **last_name**: Patient's last name (2-50 characters)
    - **email**: Unique email address
    - **phone_number**: Unique phone number in international format
    - **password**: Secure password with complexity requirements
    - **confirm_password**: Password confirmation
    - **date_of_birth**: Date of birth (must be at least 13 years old)
    - **gender**: Gender selection
    - **address**: Complete address information
    - **emergency_contact**: Optional emergency contact details
    - **medical_history**: Optional medical history notes
    - **insurance_info**: Optional insurance information
    """
    try:
        result = patient_service.register_patient(patient_data)

        if result["success"]:
            return PatientRegistrationResponse(
                success=True, message=result["message"], data=result["data"]
            )
        else:
            # Handle specific error cases
            if result.get("error_code") in ["EMAIL_EXISTS", "PHONE_EXISTS"]:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "success": False,
                        "message": result["message"],
                        "error_code": result["error_code"],
                    },
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "success": False,
                        "message": result["message"],
                        "error_code": result.get("error_code", "INTERNAL_ERROR"),
                    },
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during patient registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Registration failed due to internal error",
                "error_code": "INTERNAL_ERROR",
            },
        )


@router.post(
    "/login",
    response_model=PatientLoginResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Login successful"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        423: {"model": ErrorResponse, "description": "Account locked"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def login_patient(login_data: PatientLoginRequest):
    """
    Authenticate patient login with security features.

    - **identifier**: Email or phone number
    - **password**: Patient's password
    - **remember_me**: Optional remember me flag
    """
    try:
        result = patient_service.login_patient(login_data)

        if result["success"]:
            return PatientLoginResponse(
                success=True, message=result["message"], data=result["data"]
            )
        else:
            # Handle specific error cases
            if result.get("error_code") == "ACCOUNT_LOCKED":
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail={
                        "success": False,
                        "message": result["message"],
                        "error_code": result["error_code"],
                    },
                )
            elif result.get("error_code") in [
                "INVALID_CREDENTIALS",
                "ACCOUNT_DEACTIVATED",
            ]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "success": False,
                        "message": result["message"],
                        "error_code": result["error_code"],
                    },
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "success": False,
                        "message": result["message"],
                        "error_code": result.get("error_code", "INTERNAL_ERROR"),
                    },
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during patient login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Login failed due to internal error",
                "error_code": "INTERNAL_ERROR",
            },
        )


@router.get(
    "/profile",
    response_model=PatientDetailResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Profile retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Patient not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_patient_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Get current patient's profile information.
    Requires valid authentication token.
    """
    try:
        # Verify token and get patient ID
        patient_id = await get_current_patient_id(credentials.credentials)

        result = patient_service.get_patient_profile(patient_id)

        if result["success"]:
            return PatientDetailResponse(**result["data"])
        else:
            if result.get("error_code") == "PATIENT_NOT_FOUND":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "message": result["message"],
                        "error_code": result["error_code"],
                    },
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "success": False,
                        "message": result["message"],
                        "error_code": result.get("error_code", "INTERNAL_ERROR"),
                    },
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving patient profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Failed to retrieve profile due to internal error",
                "error_code": "INTERNAL_ERROR",
            },
        )


@router.put(
    "/profile",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Profile updated successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Patient not found"},
        409: {"model": ErrorResponse, "description": "Phone number already exists"},
        422: {"model": ValidationErrorResponse, "description": "Validation failed"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_patient_profile(
    update_data: PatientUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Update current patient's profile information.
    Requires valid authentication token.
    """
    try:
        # Verify token and get patient ID
        patient_id = await get_current_patient_id(credentials.credentials)

        result = patient_service.update_patient_profile(patient_id, update_data)

        if result["success"]:
            return {"success": True, "message": result["message"]}
        else:
            # Handle specific error cases
            if result.get("error_code") == "PATIENT_NOT_FOUND":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "message": result["message"],
                        "error_code": result["error_code"],
                    },
                )
            elif result.get("error_code") == "PHONE_EXISTS":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "success": False,
                        "message": result["message"],
                        "error_code": result["error_code"],
                    },
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "success": False,
                        "message": result["message"],
                        "error_code": result.get("error_code", "INTERNAL_ERROR"),
                    },
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating patient profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Profile update failed due to internal error",
                "error_code": "INTERNAL_ERROR",
            },
        )


@router.post(
    "/logout",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Logout successful"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def logout_patient(
    refresh_token: str, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Logout patient by revoking refresh token.
    Requires valid authentication token.
    """
    try:
        # Verify token and get patient ID
        patient_id = await get_current_patient_id(credentials.credentials)

        result = patient_service.logout_patient(refresh_token)

        return {"success": result["success"], "message": result["message"]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during patient logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Logout failed due to internal error",
                "error_code": "INTERNAL_ERROR",
            },
        )


@router.get("/health", response_model=dict, status_code=status.HTTP_200_OK)
async def patient_health_check():
    """
    Health check endpoint for patient service.
    """
    return {
        "status": "healthy",
        "service": "patient-registration",
        "version": "1.0.0",
        "endpoints": [
            "POST /api/v1/patient/register",
            "POST /api/v1/patient/login",
            "GET /api/v1/patient/profile",
            "PUT /api/v1/patient/profile",
            "POST /api/v1/patient/logout",
        ],
    }
