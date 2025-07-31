from pydantic import BaseModel, EmailStr, Field, validator, model_validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum
import re
from app.core.database import VerificationStatus


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class PatientAddress(BaseModel):
    street: str = Field(..., min_length=1, max_length=200, description="Street address")
    city: str = Field(..., min_length=1, max_length=100, description="City name")
    state: str = Field(
        ..., min_length=1, max_length=50, description="State or province"
    )
    zip: str = Field(..., min_length=1, max_length=20, description="Postal code")

    @validator("zip")
    def validate_zip_code(cls, v):
        # US ZIP code validation (basic)
        zip_pattern = r"^\d{5}(-\d{4})?$"
        if not re.match(zip_pattern, v):
            raise ValueError("Invalid ZIP code format. Use format: 12345 or 12345-6789")
        return v


class EmergencyContact(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, description="Emergency contact name"
    )
    phone: str = Field(..., description="Emergency contact phone number")
    relationship: str = Field(
        ..., min_length=1, max_length=50, description="Relationship to patient"
    )

    @validator("phone")
    def validate_emergency_phone(cls, v):
        # Basic international phone number validation
        phone_pattern = r"^\+?[1-9]\d{1,14}$"
        cleaned_phone = (
            v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        )
        if not re.match(phone_pattern, cleaned_phone):
            raise ValueError(
                "Invalid phone number format. Use international format (e.g., +1234567890)"
            )
        return cleaned_phone


class InsuranceInfo(BaseModel):
    provider: str = Field(
        ..., min_length=1, max_length=100, description="Insurance provider name"
    )
    policy_number: str = Field(
        ..., min_length=1, max_length=50, description="Insurance policy number"
    )


class PatientRegistrationRequest(BaseModel):
    first_name: str = Field(
        ..., min_length=2, max_length=50, description="Patient's first name"
    )
    last_name: str = Field(
        ..., min_length=2, max_length=50, description="Patient's last name"
    )
    email: EmailStr = Field(..., description="Patient's email address")
    phone_number: str = Field(..., description="Patient's phone number")
    password: str = Field(..., min_length=8, description="Patient's password")
    confirm_password: str = Field(..., description="Password confirmation")
    date_of_birth: date = Field(..., description="Patient's date of birth")
    gender: Gender = Field(..., description="Patient's gender")
    address: PatientAddress = Field(..., description="Patient's address")
    emergency_contact: Optional[EmergencyContact] = Field(
        None, description="Emergency contact information"
    )
    medical_history: Optional[List[str]] = Field(
        default=[], description="Medical history notes"
    )
    insurance_info: Optional[InsuranceInfo] = Field(
        None, description="Insurance information"
    )

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
        phone_pattern = r"^\+?[1-9]\d{1,14}$"
        cleaned_phone = (
            v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        )
        if not re.match(phone_pattern, cleaned_phone):
            raise ValueError(
                "Invalid phone number format. Use international format (e.g., +1234567890)"
            )
        return cleaned_phone

    @validator("date_of_birth")
    def validate_date_of_birth(cls, v):
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))

        if age < 13:
            raise ValueError("Must be at least 13 years old for COPPA compliance")

        if v >= today:
            raise ValueError("Date of birth must be in the past")

        return v

    @model_validator(mode="after")
    def validate_medical_history(self):
        medical_history = self.medical_history
        if medical_history:
            # Validate each medical history entry
            for i, entry in enumerate(medical_history):
                if not entry.strip():
                    raise ValueError(f"Medical history entry {i + 1} cannot be empty")
                if len(entry) > 500:
                    raise ValueError(
                        f"Medical history entry {i + 1} is too long (max 500 characters)"
                    )
        return self


class PatientResponse(BaseModel):
    patient_id: str
    email: str
    phone_number: str
    email_verified: bool
    phone_verified: bool

    class Config:
        from_attributes = True


class PatientRegistrationResponse(BaseModel):
    success: bool
    message: str
    data: PatientResponse


class PatientLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Patient's email address")
    password: str = Field(..., min_length=1, description="Patient's password")

    @validator("password")
    def validate_password_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Password cannot be empty")
        return v.strip()


class PatientInfo(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    date_of_birth: date
    gender: Gender
    email_verified: bool
    phone_verified: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PatientLoginData(BaseModel):
    access_token: str
    expires_in: int
    token_type: str
    patient: dict


class PatientLoginResponse(BaseModel):
    success: bool
    message: str
    data: PatientLoginData


class PatientDetailResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    phone_number: str
    date_of_birth: date
    gender: Gender
    address: PatientAddress
    emergency_contact: Optional[EmergencyContact]
    medical_history: List[str]
    insurance_info: Optional[InsuranceInfo]
    email_verified: bool
    phone_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PatientUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    phone_number: Optional[str] = Field(None)
    address: Optional[PatientAddress] = None
    emergency_contact: Optional[EmergencyContact] = None
    medical_history: Optional[List[str]] = None
    insurance_info: Optional[InsuranceInfo] = None

    @validator("phone_number")
    def validate_phone_number(cls, v):
        if v is not None:
            phone_pattern = r"^\+?[1-9]\d{1,14}$"
            cleaned_phone = (
                v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            )
            if not re.match(phone_pattern, cleaned_phone):
                raise ValueError(
                    "Invalid phone number format. Use international format (e.g., +1234567890)"
                )
            return cleaned_phone
        return v


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None
    errors: Optional[dict] = None


class ValidationErrorResponse(BaseModel):
    success: bool = False
    message: str = "Validation failed"
    errors: dict
