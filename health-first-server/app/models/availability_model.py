from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Text,
    Enum,
    Date,
    JSON,
    ForeignKey,
    Numeric,
    Time,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pymongo import MongoClient
from typing import Optional, Union, Dict, Any, List
import uuid
from datetime import datetime, date, time
import enum
from bson import ObjectId
import pytz

from app.core.config import settings
from app.core.database import Base


class RecurrencePattern(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class SlotStatus(str, enum.Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    MAINTENANCE = "maintenance"


class AppointmentType(str, enum.Enum):
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"
    TELEMEDICINE = "telemedicine"


class LocationType(str, enum.Enum):
    CLINIC = "clinic"
    HOSPITAL = "hospital"
    TELEMEDICINE = "telemedicine"
    HOME_VISIT = "home_visit"


class ProviderAvailabilitySQL(Base):
    """SQLAlchemy model for Provider Availability in relational databases"""

    __tablename__ = "provider_availability"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(
        String(36), ForeignKey("providers.id"), nullable=False, index=True
    )
    date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    timezone = Column(String(50), nullable=False, default="UTC")
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(Enum(RecurrencePattern), nullable=True)
    recurrence_end_date = Column(Date, nullable=True)
    slot_duration = Column(Integer, default=30)  # minutes
    break_duration = Column(Integer, default=0)  # minutes
    status = Column(Enum(SlotStatus), default=SlotStatus.AVAILABLE)
    max_appointments_per_slot = Column(Integer, default=1)
    current_appointments = Column(Integer, default=0)
    appointment_type = Column(
        Enum(AppointmentType), default=AppointmentType.CONSULTATION
    )

    # Location information as JSON
    location = Column(JSON, nullable=True)

    # Pricing information as JSON
    pricing = Column(JSON, nullable=True)

    notes = Column(Text, nullable=True)
    special_requirements = Column(JSON, default=list)  # Store as JSON array

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship
    appointment_slots = relationship(
        "AppointmentSlotSQL", back_populates="availability"
    )


class AppointmentSlotSQL(Base):
    """SQLAlchemy model for Appointment Slots in relational databases"""

    __tablename__ = "appointment_slots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    availability_id = Column(
        String(36), ForeignKey("provider_availability.id"), nullable=False, index=True
    )
    provider_id = Column(
        String(36), ForeignKey("providers.id"), nullable=False, index=True
    )
    slot_start_time = Column(DateTime, nullable=False, index=True)
    slot_end_time = Column(DateTime, nullable=False, index=True)
    status = Column(Enum(SlotStatus), default=SlotStatus.AVAILABLE)
    patient_id = Column(
        String(36), ForeignKey("patients.id"), nullable=True, index=True
    )
    appointment_type = Column(String(50), nullable=False)
    booking_reference = Column(String(100), unique=True, nullable=True, index=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    availability = relationship(
        "ProviderAvailabilitySQL", back_populates="appointment_slots"
    )


# MongoDB Models (for NoSQL databases)
class ProviderAvailabilityMongoDB:
    """MongoDB model for Provider Availability"""

    def __init__(self, collection):
        self.collection = collection

    def create_availability(self, availability_data: Dict[str, Any]) -> str:
        """Create a new availability record"""
        availability_data["_id"] = str(ObjectId())
        availability_data["created_at"] = datetime.utcnow()
        availability_data["updated_at"] = datetime.utcnow()

        result = self.collection.insert_one(availability_data)
        return str(result.inserted_id)

    def get_availability_by_id(self, availability_id: str) -> Optional[Dict[str, Any]]:
        """Get availability by ID"""
        return self.collection.find_one({"_id": availability_id})

    def get_provider_availability(
        self,
        provider_id: str,
        start_date: date,
        end_date: date,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get provider availability within date range"""
        query = {
            "provider_id": provider_id,
            "date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()},
        }

        if status:
            query["status"] = status

        return list(self.collection.find(query).sort("date", 1))

    def update_availability(
        self, availability_id: str, update_data: Dict[str, Any]
    ) -> bool:
        """Update availability record"""
        update_data["updated_at"] = datetime.utcnow()
        result = self.collection.update_one(
            {"_id": availability_id}, {"$set": update_data}
        )
        return result.modified_count > 0

    def delete_availability(self, availability_id: str) -> bool:
        """Delete availability record"""
        result = self.collection.delete_one({"_id": availability_id})
        return result.deleted_count > 0

    def find_conflicting_slots(
        self,
        provider_id: str,
        date: date,
        start_time: time,
        end_time: time,
        exclude_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Find conflicting availability slots"""
        query = {
            "provider_id": provider_id,
            "date": date.isoformat(),
            "$or": [
                {
                    "start_time": {"$lt": end_time.isoformat()},
                    "end_time": {"$gt": start_time.isoformat()},
                }
            ],
        }

        if exclude_id:
            query["_id"] = {"$ne": exclude_id}

        return list(self.collection.find(query))


class AppointmentSlotMongoDB:
    """MongoDB model for Appointment Slots"""

    def __init__(self, collection):
        self.collection = collection

    def create_slot(self, slot_data: Dict[str, Any]) -> str:
        """Create a new appointment slot"""
        slot_data["_id"] = str(ObjectId())
        slot_data["created_at"] = datetime.utcnow()
        slot_data["updated_at"] = datetime.utcnow()

        result = self.collection.insert_one(slot_data)
        return str(result.inserted_id)

    def get_slot_by_id(self, slot_id: str) -> Optional[Dict[str, Any]]:
        """Get appointment slot by ID"""
        return self.collection.find_one({"_id": slot_id})

    def get_available_slots(
        self,
        provider_id: Optional[str] = None,
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
        appointment_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get available appointment slots"""
        query = {"status": "available"}

        if provider_id:
            query["provider_id"] = provider_id

        if start_datetime:
            query["slot_start_time"] = {"$gte": start_datetime}

        if end_datetime:
            if "slot_start_time" in query:
                query["slot_start_time"]["$lte"] = end_datetime
            else:
                query["slot_start_time"] = {"$lte": end_datetime}

        if appointment_type:
            query["appointment_type"] = appointment_type

        return list(self.collection.find(query).sort("slot_start_time", 1))

    def update_slot(self, slot_id: str, update_data: Dict[str, Any]) -> bool:
        """Update appointment slot"""
        update_data["updated_at"] = datetime.utcnow()
        result = self.collection.update_one({"_id": slot_id}, {"$set": update_data})
        return result.modified_count > 0

    def delete_slot(self, slot_id: str) -> bool:
        """Delete appointment slot"""
        result = self.collection.delete_one({"_id": slot_id})
        return result.deleted_count > 0

    def book_slot(self, slot_id: str, patient_id: str, booking_reference: str) -> bool:
        """Book an appointment slot"""
        result = self.collection.update_one(
            {"_id": slot_id, "status": "available"},
            {
                "$set": {
                    "status": "booked",
                    "patient_id": patient_id,
                    "booking_reference": booking_reference,
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0


def get_availability_model():
    """Get the appropriate availability model based on database type"""
    if settings.database_type == "mongodb":
        collection = mongo_db["provider_availability"]
        return ProviderAvailabilityMongoDB(collection)
    else:
        return ProviderAvailabilitySQL


def get_appointment_slot_model():
    """Get the appropriate appointment slot model based on database type"""
    if settings.database_type == "mongodb":
        collection = mongo_db["appointment_slots"]
        return AppointmentSlotMongoDB(collection)
    else:
        return AppointmentSlotSQL
