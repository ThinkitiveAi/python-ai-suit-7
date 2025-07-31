from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import jwt
from datetime import datetime

from app.core.config import settings

# Security scheme
security = HTTPBearer()


def get_current_provider(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    Get the current authenticated provider from JWT token.
    This is a simplified version for demonstration purposes.
    """
    try:
        # In a real implementation, you would verify the JWT token
        # For now, we'll return a mock provider
        token = credentials.credentials

        # Mock provider data (in real implementation, this would come from JWT payload)
        provider_data = {
            "id": "test-provider-id",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "Provider",
            "specialization": "General Practice",
            "is_active": True,
        }

        return provider_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_patient(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    Get the current authenticated patient from JWT token.
    This is a simplified version for demonstration purposes.
    """
    try:
        # In a real implementation, you would verify the JWT token
        # For now, we'll return a mock patient
        token = credentials.credentials

        # Mock patient data (in real implementation, this would come from JWT payload)
        patient_data = {
            "id": "test-patient-id",
            "email": "patient@example.com",
            "first_name": "Test",
            "last_name": "Patient",
            "is_active": True,
        }

        return patient_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_provider_permission(
    provider_id: str, current_provider: Dict[str, Any] = Depends(get_current_provider)
) -> bool:
    """
    Verify that the current provider has permission to access the requested resource.
    """
    if current_provider["id"] != provider_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    return True


def verify_patient_permission(
    patient_id: str, current_patient: Dict[str, Any] = Depends(get_current_patient)
) -> bool:
    """
    Verify that the current patient has permission to access the requested resource.
    """
    if current_patient["id"] != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    return True
