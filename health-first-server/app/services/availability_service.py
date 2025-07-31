from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, time, timedelta
import pytz
from decimal import Decimal
import uuid
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.availability_model import (
    ProviderAvailabilitySQL,
    AppointmentSlotSQL,
    ProviderAvailabilityMongoDB,
    AppointmentSlotMongoDB,
    get_availability_model,
    get_appointment_slot_model,
    SlotStatus,
    AppointmentType,
    RecurrencePattern,
)
from app.schemas.availability_schema import (
    CreateAvailabilityRequest,
    UpdateAvailabilityRequest,
    AvailabilitySearchRequest,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class AvailabilityService:
    """Service class for managing provider availability"""

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.availability_model = get_availability_model()
        self.slot_model = get_appointment_slot_model()

    def create_availability_slots(
        self, provider_id: str, request: CreateAvailabilityRequest
    ) -> Dict[str, Any]:
        """Create availability slots for a provider"""
        try:
            # Convert times to time objects
            start_time = time.fromisoformat(request.start_time)
            end_time = time.fromisoformat(request.end_time)

            # Validate time range
            if end_time <= start_time:
                raise ValueError("End time must be after start time")

            # Check for conflicts
            conflicts = self._find_conflicting_slots(
                provider_id, request.date, start_time, end_time
            )
            if conflicts:
                raise ValueError(f"Conflicting slots found: {len(conflicts)} conflicts")

            slots_created = 0
            availability_id = None

            if request.is_recurring:
                # Handle recurring availability
                slots_created, availability_id = self._create_recurring_slots(
                    provider_id, request
                )
            else:
                # Handle single availability
                slots_created, availability_id = self._create_single_availability(
                    provider_id, request
                )

            return {
                "availability_id": availability_id,
                "slots_created": slots_created,
                "date_range": {
                    "start": request.date.isoformat(),
                    "end": request.recurrence_end_date.isoformat()
                    if request.is_recurring
                    else request.date.isoformat(),
                },
                "total_appointments_available": slots_created
                * request.max_appointments_per_slot,
            }

        except Exception as e:
            logger.error(f"Error creating availability slots: {str(e)}")
            raise

    def _create_single_availability(
        self, provider_id: str, request: CreateAvailabilityRequest
    ) -> Tuple[int, str]:
        """Create a single availability record"""
        if settings.database_type in ["postgresql", "mysql"]:
            # SQLAlchemy implementation
            availability = ProviderAvailabilitySQL(
                provider_id=provider_id,
                date=request.date,
                start_time=time.fromisoformat(request.start_time),
                end_time=time.fromisoformat(request.end_time),
                timezone=request.timezone,
                slot_duration=request.slot_duration,
                break_duration=request.break_duration,
                appointment_type=request.appointment_type,
                location=request.location.dict() if request.location else None,
                pricing=request.pricing.dict() if request.pricing else None,
                notes=request.notes,
                special_requirements=request.special_requirements,
                max_appointments_per_slot=request.max_appointments_per_slot,
            )

            self.db.add(availability)
            self.db.commit()
            self.db.refresh(availability)

            # Generate appointment slots
            slots_created = self._generate_appointment_slots(availability)

            return slots_created, availability.id
        else:
            # MongoDB implementation
            availability_data = {
                "provider_id": provider_id,
                "date": request.date.isoformat(),
                "start_time": request.start_time,
                "end_time": request.end_time,
                "timezone": request.timezone,
                "slot_duration": request.slot_duration,
                "break_duration": request.break_duration,
                "appointment_type": request.appointment_type.value,
                "location": request.location.dict() if request.location else None,
                "pricing": request.pricing.dict() if request.pricing else None,
                "notes": request.notes,
                "special_requirements": request.special_requirements,
                "max_appointments_per_slot": request.max_appointments_per_slot,
                "status": SlotStatus.AVAILABLE.value,
            }

            availability_id = self.availability_model.create_availability(
                availability_data
            )
            slots_created = self._generate_appointment_slots_mongo(
                availability_data, availability_id
            )

            return slots_created, availability_id

    def _create_recurring_slots(
        self, provider_id: str, request: CreateAvailabilityRequest
    ) -> Tuple[int, str]:
        """Create recurring availability slots"""
        current_date = request.date
        end_date = request.recurrence_end_date
        slots_created = 0
        availability_id = None

        while current_date <= end_date:
            # Check if this date should have availability based on pattern
            if self._should_create_slot_for_date(
                current_date, request.date, request.recurrence_pattern
            ):
                try:
                    single_request = CreateAvailabilityRequest(
                        date=current_date,
                        start_time=request.start_time,
                        end_time=request.end_time,
                        timezone=request.timezone,
                        slot_duration=request.slot_duration,
                        break_duration=request.break_duration,
                        is_recurring=False,  # Set to False to avoid infinite recursion
                        appointment_type=request.appointment_type,
                        location=request.location,
                        pricing=request.pricing,
                        special_requirements=request.special_requirements,
                        notes=request.notes,
                        max_appointments_per_slot=request.max_appointments_per_slot,
                    )

                    single_slots, single_id = self._create_single_availability(
                        provider_id, single_request
                    )
                    slots_created += single_slots

                    if availability_id is None:
                        availability_id = single_id

                except Exception as e:
                    logger.warning(
                        f"Failed to create slot for {current_date}: {str(e)}"
                    )

            # Move to next date based on pattern
            current_date = self._get_next_date(current_date, request.recurrence_pattern)

        return slots_created, availability_id or str(uuid.uuid4())

    def _should_create_slot_for_date(
        self, current_date: date, start_date: date, pattern: RecurrencePattern
    ) -> bool:
        """Determine if a slot should be created for the given date based on pattern"""
        if pattern == RecurrencePattern.DAILY:
            return True
        elif pattern == RecurrencePattern.WEEKLY:
            return current_date.weekday() == start_date.weekday()
        elif pattern == RecurrencePattern.MONTHLY:
            return current_date.day == start_date.day
        return False

    def _get_next_date(self, current_date: date, pattern: RecurrencePattern) -> date:
        """Get the next date based on recurrence pattern"""
        if pattern == RecurrencePattern.DAILY:
            return current_date + timedelta(days=1)
        elif pattern == RecurrencePattern.WEEKLY:
            return current_date + timedelta(weeks=1)
        elif pattern == RecurrencePattern.MONTHLY:
            # Simple monthly increment (may need refinement for month-end dates)
            year = current_date.year
            month = current_date.month + 1
            if month > 12:
                month = 1
                year += 1
            return current_date.replace(year=year, month=month)
        return current_date + timedelta(days=1)

    def _generate_appointment_slots(self, availability: ProviderAvailabilitySQL) -> int:
        """Generate individual appointment slots from availability"""
        slots_created = 0
        current_time = availability.start_time

        while current_time < availability.end_time:
            slot_end_time = self._add_minutes_to_time(
                current_time, availability.slot_duration
            )

            if slot_end_time > availability.end_time:
                break

            # Create appointment slot
            slot = AppointmentSlotSQL(
                availability_id=availability.id,
                provider_id=availability.provider_id,
                slot_start_time=self._combine_date_time(
                    availability.date, current_time, availability.timezone
                ),
                slot_end_time=self._combine_date_time(
                    availability.date, slot_end_time, availability.timezone
                ),
                appointment_type=availability.appointment_type.value,
                status=SlotStatus.AVAILABLE,
            )

            self.db.add(slot)
            slots_created += 1

            # Add break time
            if availability.break_duration > 0:
                current_time = self._add_minutes_to_time(
                    slot_end_time, availability.break_duration
                )
            else:
                current_time = slot_end_time

        self.db.commit()
        return slots_created

    def _generate_appointment_slots_mongo(
        self, availability_data: Dict[str, Any], availability_id: str
    ) -> int:
        """Generate individual appointment slots from availability (MongoDB)"""
        slots_created = 0
        start_time = time.fromisoformat(availability_data["start_time"])
        end_time = time.fromisoformat(availability_data["end_time"])
        current_time = start_time

        while current_time < end_time:
            slot_end_time = self._add_minutes_to_time(
                current_time, availability_data["slot_duration"]
            )

            if slot_end_time > end_time:
                break

            # Create appointment slot
            slot_data = {
                "availability_id": availability_id,
                "provider_id": availability_data["provider_id"],
                "slot_start_time": self._combine_date_time(
                    date.fromisoformat(availability_data["date"]),
                    current_time,
                    availability_data["timezone"],
                ),
                "slot_end_time": self._combine_date_time(
                    date.fromisoformat(availability_data["date"]),
                    slot_end_time,
                    availability_data["timezone"],
                ),
                "appointment_type": availability_data["appointment_type"],
                "status": SlotStatus.AVAILABLE.value,
            }

            self.slot_model.create_slot(slot_data)
            slots_created += 1

            # Add break time
            if availability_data["break_duration"] > 0:
                current_time = self._add_minutes_to_time(
                    slot_end_time, availability_data["break_duration"]
                )
            else:
                current_time = slot_end_time

        return slots_created

    def _add_minutes_to_time(self, t: time, minutes: int) -> time:
        """Add minutes to a time object"""
        total_minutes = t.hour * 60 + t.minute + minutes
        hours = total_minutes // 60
        mins = total_minutes % 60
        return time(hour=hours, minute=mins)

    def _combine_date_time(self, d: date, t: time, timezone_str: str) -> datetime:
        """Combine date and time into a timezone-aware datetime"""
        naive_dt = datetime.combine(d, t)
        tz = pytz.timezone(timezone_str)
        return tz.localize(naive_dt)

    def _find_conflicting_slots(
        self, provider_id: str, date: date, start_time: time, end_time: time
    ) -> List[Dict[str, Any]]:
        """Find conflicting availability slots"""
        if settings.database_type in ["postgresql", "mysql"]:
            conflicts = (
                self.db.query(ProviderAvailabilitySQL)
                .filter(
                    and_(
                        ProviderAvailabilitySQL.provider_id == provider_id,
                        ProviderAvailabilitySQL.date == date,
                        or_(
                            and_(
                                ProviderAvailabilitySQL.start_time < end_time,
                                ProviderAvailabilitySQL.end_time > start_time,
                            )
                        ),
                    )
                )
                .all()
            )

            return [
                {"id": c.id, "start_time": c.start_time, "end_time": c.end_time}
                for c in conflicts
            ]
        else:
            return self.availability_model.find_conflicting_slots(
                provider_id, date, start_time, end_time
            )

    def get_provider_availability(
        self,
        provider_id: str,
        start_date: date,
        end_date: date,
        status: Optional[str] = None,
        appointment_type: Optional[str] = None,
        timezone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get provider availability within date range"""
        try:
            if settings.database_type in ["postgresql", "mysql"]:
                return self._get_provider_availability_sql(
                    provider_id,
                    start_date,
                    end_date,
                    status,
                    appointment_type,
                    timezone,
                )
            else:
                return self._get_provider_availability_mongo(
                    provider_id,
                    start_date,
                    end_date,
                    status,
                    appointment_type,
                    timezone,
                )
        except Exception as e:
            logger.error(f"Error getting provider availability: {str(e)}")
            raise

    def _get_provider_availability_sql(
        self,
        provider_id: str,
        start_date: date,
        end_date: date,
        status: Optional[str] = None,
        appointment_type: Optional[str] = None,
        timezone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get provider availability using SQLAlchemy"""
        query = self.db.query(ProviderAvailabilitySQL).filter(
            and_(
                ProviderAvailabilitySQL.provider_id == provider_id,
                ProviderAvailabilitySQL.date >= start_date,
                ProviderAvailabilitySQL.date <= end_date,
            )
        )

        if status:
            query = query.filter(ProviderAvailabilitySQL.status == status)
        if appointment_type:
            query = query.filter(
                ProviderAvailabilitySQL.appointment_type == appointment_type
            )

        availabilities = query.all()

        # Get appointment slots
        availability_ids = [a.id for a in availabilities]
        slots = (
            self.db.query(AppointmentSlotSQL)
            .filter(AppointmentSlotSQL.availability_id.in_(availability_ids))
            .all()
        )

        return self._format_availability_response(availabilities, slots, provider_id)

    def _get_provider_availability_mongo(
        self,
        provider_id: str,
        start_date: date,
        end_date: date,
        status: Optional[str] = None,
        appointment_type: Optional[str] = None,
        timezone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get provider availability using MongoDB"""
        availabilities = self.availability_model.get_provider_availability(
            provider_id, start_date, end_date, status
        )

        # Get appointment slots
        availability_ids = [a["_id"] for a in availabilities]
        slots = self.slot_model.get_available_slots(provider_id=provider_id)

        return self._format_availability_response(availabilities, slots, provider_id)

    def _format_availability_response(
        self, availabilities: List, slots: List, provider_id: str
    ) -> Dict[str, Any]:
        """Format availability response"""
        # Group slots by date
        daily_availability = {}
        total_slots = 0
        available_slots = 0
        booked_slots = 0
        cancelled_slots = 0

        for slot in slots:
            slot_date = (
                slot.slot_start_time.date()
                if hasattr(slot, "slot_start_time")
                else slot["slot_start_time"].date()
            )
            if slot_date not in daily_availability:
                daily_availability[slot_date] = []

            slot_data = {
                "slot_id": slot.id if hasattr(slot, "id") else slot["_id"],
                "start_time": slot.slot_start_time.strftime("%H:%M")
                if hasattr(slot, "slot_start_time")
                else slot["slot_start_time"].strftime("%H:%M"),
                "end_time": slot.slot_end_time.strftime("%H:%M")
                if hasattr(slot, "slot_end_time")
                else slot["slot_end_time"].strftime("%H:%M"),
                "status": slot.status if hasattr(slot, "status") else slot["status"],
                "appointment_type": slot.appointment_type
                if hasattr(slot, "appointment_type")
                else slot["appointment_type"],
                "location": slot.location
                if hasattr(slot, "location")
                else slot.get("location"),
                "pricing": slot.pricing
                if hasattr(slot, "pricing")
                else slot.get("pricing"),
                "special_requirements": slot.special_requirements
                if hasattr(slot, "special_requirements")
                else slot.get("special_requirements", []),
            }

            daily_availability[slot_date].append(slot_data)
            total_slots += 1

            if slot_data["status"] == SlotStatus.AVAILABLE.value:
                available_slots += 1
            elif slot_data["status"] == SlotStatus.BOOKED.value:
                booked_slots += 1
            elif slot_data["status"] == SlotStatus.CANCELLED.value:
                cancelled_slots += 1

        return {
            "provider_id": provider_id,
            "availability_summary": {
                "total_slots": total_slots,
                "available_slots": available_slots,
                "booked_slots": booked_slots,
                "cancelled_slots": cancelled_slots,
            },
            "availability": [
                {"date": date.isoformat(), "slots": slots}
                for date, slots in sorted(daily_availability.items())
            ],
        }

    def search_available_slots(
        self, search_request: AvailabilitySearchRequest
    ) -> Dict[str, Any]:
        """Search for available appointment slots"""
        try:
            # Build search criteria
            search_criteria = {}

            if search_request.date:
                search_criteria["date"] = search_request.date.isoformat()
            elif search_request.start_date and search_request.end_date:
                search_criteria["date_range"] = {
                    "start": search_request.start_date.isoformat(),
                    "end": search_request.end_date.isoformat(),
                }

            if search_request.appointment_type:
                search_criteria["appointment_type"] = (
                    search_request.appointment_type.value
                )

            if search_request.insurance_accepted is not None:
                search_criteria["insurance_accepted"] = (
                    search_request.insurance_accepted
                )

            if search_request.max_price:
                search_criteria["max_price"] = float(search_request.max_price)

            # Get available slots
            available_slots = self.slot_model.get_available_slots(
                start_datetime=search_request.start_date,
                end_datetime=search_request.end_date,
                appointment_type=search_request.appointment_type.value
                if search_request.appointment_type
                else None,
            )

            # Group by provider and format response
            providers = {}
            for slot in available_slots:
                provider_id = slot["provider_id"]
                if provider_id not in providers:
                    # Get provider info (this would need to be implemented)
                    providers[provider_id] = {
                        "id": provider_id,
                        "name": "Dr. Provider",  # Placeholder
                        "specialization": "General Practice",  # Placeholder
                        "years_of_experience": 5,  # Placeholder
                        "rating": 4.5,  # Placeholder
                        "clinic_address": "123 Medical Center Dr",  # Placeholder
                    }

                if "available_slots" not in providers[provider_id]:
                    providers[provider_id]["available_slots"] = []

                slot_data = {
                    "slot_id": slot["_id"],
                    "date": slot["slot_start_time"].date().isoformat(),
                    "start_time": slot["slot_start_time"].strftime("%H:%M"),
                    "end_time": slot["slot_end_time"].strftime("%H:%M"),
                    "appointment_type": slot["appointment_type"],
                    "location": slot.get("location"),
                    "pricing": slot.get("pricing"),
                    "special_requirements": slot.get("special_requirements", []),
                }

                providers[provider_id]["available_slots"].append(slot_data)

            return {
                "search_criteria": search_criteria,
                "total_results": len(providers),
                "results": [
                    {
                        "provider": provider_info,
                        "available_slots": provider_info["available_slots"],
                    }
                    for provider_info in providers.values()
                ],
            }

        except Exception as e:
            logger.error(f"Error searching available slots: {str(e)}")
            raise

    def update_availability_slot(
        self, slot_id: str, request: UpdateAvailabilityRequest
    ) -> bool:
        """Update a specific availability slot"""
        try:
            update_data = {}

            if request.start_time:
                update_data["start_time"] = request.start_time
            if request.end_time:
                update_data["end_time"] = request.end_time
            if request.status:
                update_data["status"] = request.status.value
            if request.notes:
                update_data["notes"] = request.notes
            if request.pricing:
                update_data["pricing"] = request.pricing.dict()
            if request.special_requirements:
                update_data["special_requirements"] = request.special_requirements

            if settings.database_type in ["postgresql", "mysql"]:
                # SQLAlchemy implementation
                slot = (
                    self.db.query(AppointmentSlotSQL)
                    .filter(AppointmentSlotSQL.id == slot_id)
                    .first()
                )

                if not slot:
                    raise ValueError("Slot not found")

                for key, value in update_data.items():
                    setattr(slot, key, value)

                self.db.commit()
                return True
            else:
                # MongoDB implementation
                return self.slot_model.update_slot(slot_id, update_data)

        except Exception as e:
            logger.error(f"Error updating availability slot: {str(e)}")
            raise

    def delete_availability_slot(
        self, slot_id: str, delete_recurring: bool = False, reason: Optional[str] = None
    ) -> bool:
        """Delete an availability slot"""
        try:
            if settings.database_type in ["postgresql", "mysql"]:
                # SQLAlchemy implementation
                slot = (
                    self.db.query(AppointmentSlotSQL)
                    .filter(AppointmentSlotSQL.id == slot_id)
                    .first()
                )

                if not slot:
                    raise ValueError("Slot not found")

                if delete_recurring:
                    # Delete all slots from the same availability
                    self.db.query(AppointmentSlotSQL).filter(
                        AppointmentSlotSQL.availability_id == slot.availability_id
                    ).delete()
                else:
                    self.db.delete(slot)

                self.db.commit()
                return True
            else:
                # MongoDB implementation
                if delete_recurring:
                    slot = self.slot_model.get_slot_by_id(slot_id)
                    if slot:
                        # Delete all slots from the same availability
                        self.slot_model.collection.delete_many(
                            {"availability_id": slot["availability_id"]}
                        )
                        return True
                    return False
                else:
                    return self.slot_model.delete_slot(slot_id)

        except Exception as e:
            logger.error(f"Error deleting availability slot: {str(e)}")
            raise
