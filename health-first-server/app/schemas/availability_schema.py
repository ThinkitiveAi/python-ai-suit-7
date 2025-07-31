from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from decimal import Decimal
import pytz
from enum import Enum

from app.models.availability_model import (
    RecurrencePattern,
    SlotStatus,
    AppointmentType,
    LocationType,
)


class LocationSchema(BaseModel):
    type: LocationType = Field(..., description="Location type")
    address: Optional[str] = Field(None, max_length=500, description="Physical address")
    room_number: Optional[str] = Field(None, max_length=50, description="Room number")

    @field_validator("address")
    @classmethod
    def validate_address(cls, v, info):
        if info.data.get("type") in ["clinic", "hospital", "home_visit"] and not v:
            raise ValueError("Address is required for physical locations")
        return v


class PricingSchema(BaseModel):
    base_fee: Decimal = Field(..., ge=0, description="Base consultation fee")
    insurance_accepted: bool = Field(True, description="Whether insurance is accepted")
    currency: str = Field("USD", max_length=3, description="Currency code")


class CreateAvailabilityRequest(BaseModel):
    date: str = Field(..., description="Availability date (YYYY-MM-DD)")
    start_time: str = Field(..., description="Start time in HH:mm format")
    end_time: str = Field(..., description="End time in HH:mm format")
    timezone: str = Field(..., description="Timezone (e.g., America/New_York)")
    slot_duration: int = Field(
        30, ge=15, le=240, description="Slot duration in minutes"
    )
    break_duration: int = Field(0, ge=0, le=60, description="Break duration in minutes")
    is_recurring: bool = Field(
        False, description="Whether this is a recurring availability"
    )
    recurrence_pattern: Optional[RecurrencePattern] = None
    recurrence_end_date: Optional[str] = None
    appointment_type: AppointmentType = Field(
        AppointmentType.CONSULTATION, description="Appointment type"
    )
    location: LocationSchema = Field(..., description="Location information")
    pricing: Optional[PricingSchema] = None
    special_requirements: List[str] = Field(
        default_factory=list, description="Special requirements"
    )
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")
    max_appointments_per_slot: int = Field(
        1, ge=1, le=10, description="Max appointments per slot"
    )

    @field_validator("date", "recurrence_end_date")
    @classmethod
    def validate_date_format(cls, v):
        if v is not None:
            try:
                date.fromisoformat(v)
                return v
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time_format(cls, v):
        try:
            time.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError("Time must be in HH:mm format")

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, v, info):
        if "start_time" in info.data:
            start = time.fromisoformat(info.data["start_time"])
            end = time.fromisoformat(v)
            if end <= start:
                raise ValueError("End time must be after start time")
        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v):
        try:
            pytz.timezone(v)
            return v
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError("Invalid timezone")

    @field_validator("recurrence_end_date")
    @classmethod
    def validate_recurrence_end_date(cls, v, info):
        if info.data.get("is_recurring") and not v:
            raise ValueError(
                "Recurrence end date is required for recurring availability"
            )
        if v and "date" in info.data and v <= info.data["date"]:
            raise ValueError("Recurrence end date must be after start date")
        return v

    @model_validator(mode="after")
    def validate_recurring_fields(self):
        if self.is_recurring and not self.recurrence_pattern:
            raise ValueError(
                "Recurrence pattern is required for recurring availability"
            )
        return self


class UpdateAvailabilityRequest(BaseModel):
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: Optional[SlotStatus] = None
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")
    pricing: Optional[PricingSchema] = None
    special_requirements: Optional[List[str]] = None

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time_format(cls, v):
        if v is not None:
            try:
                time.fromisoformat(v)
                return v
            except ValueError:
                raise ValueError("Time must be in HH:mm format")
        return v


class AvailabilitySlotResponse(BaseModel):
    slot_id: str
    start_time: str
    end_time: str
    status: SlotStatus
    appointment_type: AppointmentType
    location: LocationSchema
    pricing: Optional[PricingSchema]
    special_requirements: List[str]

    model_config = {"from_attributes": True}


class DailyAvailabilityResponse(BaseModel):
    date: str
    slots: List[AvailabilitySlotResponse]


class AvailabilitySummaryResponse(BaseModel):
    total_slots: int
    available_slots: int
    booked_slots: int
    cancelled_slots: int


class ProviderAvailabilityResponse(BaseModel):
    provider_id: str
    availability_summary: AvailabilitySummaryResponse
    availability: List[DailyAvailabilityResponse]

    model_config = {"from_attributes": True}


class CreateAvailabilityResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any]


class ProviderInfoResponse(BaseModel):
    id: str
    name: str
    specialization: str
    years_of_experience: int
    rating: Optional[float]
    clinic_address: str


class SearchResultSlotResponse(BaseModel):
    slot_id: str
    date: str
    start_time: str
    end_time: str
    appointment_type: AppointmentType
    location: LocationSchema
    pricing: Optional[PricingSchema]
    special_requirements: List[str]


class SearchResultProviderResponse(BaseModel):
    provider: ProviderInfoResponse
    available_slots: List[SearchResultSlotResponse]


class SearchCriteriaResponse(BaseModel):
    date: Optional[str]
    specialization: Optional[str]
    location: Optional[str]
    appointment_type: Optional[str]
    insurance_accepted: Optional[bool]
    max_price: Optional[Decimal]


class AvailabilitySearchResponse(BaseModel):
    success: bool
    data: Dict[str, Any]


class DeleteAvailabilityRequest(BaseModel):
    delete_recurring: bool = Field(False, description="Delete all recurring instances")
    reason: Optional[str] = Field(
        None, max_length=200, description="Reason for deletion"
    )


class AvailabilitySearchRequest(BaseModel):
    date: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    specialization: Optional[str] = None
    location: Optional[str] = None
    appointment_type: Optional[AppointmentType] = None
    insurance_accepted: Optional[bool] = None
    max_price: Optional[Decimal] = Field(None, ge=0, description="Maximum price")
    timezone: Optional[str] = None
    available_only: bool = Field(True, description="Show only available slots")

    @field_validator("date", "start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v):
        if v is not None:
            try:
                date.fromisoformat(v)
                return v
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v):
        if v is not None:
            try:
                pytz.timezone(v)
                return v
            except pytz.exceptions.UnknownTimeZoneError:
                raise ValueError("Invalid timezone")
        return v

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("Start date must be before or equal to end date")
        return self


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
