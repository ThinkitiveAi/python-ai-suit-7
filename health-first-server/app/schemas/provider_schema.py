from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Union
from datetime import datetime
from app.core.database import VerificationStatus


class ClinicAddress(BaseModel):
    street: str = Field(..., min_length=1, max_length=200, description="Street address")
    city: str = Field(..., min_length=1, max_length=100, description="City name")
    state: str = Field(
        ..., min_length=1, max_length=50, description="State or province"
    )
    zip: str = Field(..., min_length=1, max_length=20, description="Postal code")


class ProviderRegistrationRequest(BaseModel):
    first_name: str = Field(
        ..., min_length=2, max_length=50, description="Provider's first name"
    )
    last_name: str = Field(
        ..., min_length=2, max_length=50, description="Provider's last name"
    )
    email: EmailStr = Field(..., description="Provider's email address")
    phone_number: str = Field(..., description="Provider's phone number")
    password: str = Field(..., min_length=8, description="Provider's password")
    confirm_password: str = Field(..., description="Password confirmation")
    specialization: str = Field(
        ..., min_length=3, max_length=100, description="Medical specialization"
    )
    license_number: str = Field(..., description="Medical license number")
    years_of_experience: int = Field(
        ..., ge=0, le=50, description="Years of experience"
    )
    clinic_address: ClinicAddress = Field(..., description="Clinic address information")

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v

    @validator("confirm_password")
    def validate_confirm_password(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v

    @validator("phone_number")
    def validate_phone_number(cls, v):
        # Basic international phone number validation
        import re

        phone_pattern = r"^\+?[1-9]\d{1,14}$"
        if not re.match(
            phone_pattern,
            v.replace(" ", "").replace("-", "").replace("(", "").replace(")", ""),
        ):
            raise ValueError(
                "Invalid phone number format. Use international format (e.g., +1234567890)"
            )
        return v

    @validator("license_number")
    def validate_license_number(cls, v):
        import re

        if not re.match(r"^[A-Za-z0-9]+$", v):
            raise ValueError("License number must be alphanumeric")
        return v.upper()

    @validator("specialization")
    def validate_specialization(cls, v):
        # Predefined list of medical specializations
        valid_specializations = [
            "Cardiology",
            "Dermatology",
            "Endocrinology",
            "Gastroenterology",
            "General Practice",
            "Internal Medicine",
            "Neurology",
            "Oncology",
            "Orthopedics",
            "Pediatrics",
            "Psychiatry",
            "Radiology",
            "Surgery",
            "Urology",
            "Obstetrics and Gynecology",
            "Emergency Medicine",
            "Family Medicine",
            "Anesthesiology",
            "Pathology",
            "Ophthalmology",
        ]
        if v not in valid_specializations:
            raise ValueError(
                f"Specialization must be one of: {', '.join(valid_specializations)}"
            )
        return v


class ProviderResponse(BaseModel):
    provider_id: str
    email: str
    verification_status: VerificationStatus

    class Config:
        from_attributes = True


class ProviderRegistrationResponse(BaseModel):
    success: bool
    message: str
    data: ProviderResponse


class ProviderLoginRequest(BaseModel):
    identifier: str = Field(..., description="Email or phone number")
    password: str = Field(..., min_length=1)
    remember_me: Optional[bool] = False


class ProviderInfo(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: EmailStr
    specialization: str
    verification_status: str
    is_active: bool


class ProviderLoginResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict]


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict]


class ProviderLogoutRequest(BaseModel):
    refresh_token: str


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None


class ProviderDetailResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    phone_number: str
    specialization: str
    license_number: str
    years_of_experience: int
    clinic_address: ClinicAddress
    verification_status: VerificationStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
