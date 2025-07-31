import pytest
from datetime import datetime, date, time, timedelta
from decimal import Decimal
import pytz
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.availability_model import (
    ProviderAvailabilitySQL,
    AppointmentSlotSQL,
    SlotStatus,
    AppointmentType,
    RecurrencePattern,
    LocationType,
)
from app.schemas.availability_schema import (
    CreateAvailabilityRequest,
    LocationSchema,
    PricingSchema,
)
from app.services.availability_service import AvailabilityService


class TestAvailabilityModels:
    """Test cases for availability models"""

    def test_provider_availability_sql_creation(self):
        """Test creating a ProviderAvailabilitySQL instance"""
        availability = ProviderAvailabilitySQL(
            provider_id="test-provider-id",
            date=date(2024, 2, 15),
            start_time=time(9, 0),
            end_time=time(17, 0),
            timezone="America/New_York",
            slot_duration=30,
            appointment_type=AppointmentType.CONSULTATION,
        )

        assert availability.provider_id == "test-provider-id"
        assert availability.date == date(2024, 2, 15)
        assert availability.start_time == time(9, 0)
        assert availability.end_time == time(17, 0)
        assert availability.timezone == "America/New_York"
        assert availability.slot_duration == 30
        assert availability.appointment_type == AppointmentType.CONSULTATION
        assert availability.status == SlotStatus.AVAILABLE


class TestAvailabilitySchemas:
    """Test cases for availability schemas"""

    def test_create_availability_request_valid(self):
        """Test valid CreateAvailabilityRequest"""
        request = CreateAvailabilityRequest(
            date=date(2024, 2, 15),
            start_time="09:00",
            end_time="17:00",
            timezone="America/New_York",
            slot_duration=30,
            appointment_type=AppointmentType.CONSULTATION,
            location=LocationSchema(
                type=LocationType.CLINIC,
                address="123 Medical Center Dr",
                room_number="Room 205",
            ),
            pricing=PricingSchema(
                base_fee=Decimal("150.00"), insurance_accepted=True, currency="USD"
            ),
        )

        assert request.date == date(2024, 2, 15)
        assert request.start_time == "09:00"
        assert request.end_time == "17:00"
        assert request.timezone == "America/New_York"
        assert request.slot_duration == 30
        assert request.appointment_type == AppointmentType.CONSULTATION

    def test_create_availability_request_invalid_time_format(self):
        """Test CreateAvailabilityRequest with invalid time format"""
        with pytest.raises(ValueError, match="Time must be in HH:mm format"):
            CreateAvailabilityRequest(
                date=date(2024, 2, 15),
                start_time="9:00",  # Missing leading zero
                end_time="17:00",
                timezone="America/New_York",
                appointment_type=AppointmentType.CONSULTATION,
                location=LocationSchema(
                    type=LocationType.CLINIC, address="123 Medical Center Dr"
                ),
            )

    def test_create_availability_request_end_time_before_start_time(self):
        """Test CreateAvailabilityRequest with end time before start time"""
        with pytest.raises(ValueError, match="End time must be after start time"):
            CreateAvailabilityRequest(
                date=date(2024, 2, 15),
                start_time="17:00",
                end_time="09:00",  # Before start time
                timezone="America/New_York",
                appointment_type=AppointmentType.CONSULTATION,
                location=LocationSchema(
                    type=LocationType.CLINIC, address="123 Medical Center Dr"
                ),
            )

    def test_create_availability_request_invalid_timezone(self):
        """Test CreateAvailabilityRequest with invalid timezone"""
        with pytest.raises(ValueError, match="Invalid timezone"):
            CreateAvailabilityRequest(
                date=date(2024, 2, 15),
                start_time="09:00",
                end_time="17:00",
                timezone="Invalid/Timezone",
                appointment_type=AppointmentType.CONSULTATION,
                location=LocationSchema(
                    type=LocationType.CLINIC, address="123 Medical Center Dr"
                ),
            )


class TestAvailabilityService:
    """Test cases for AvailabilityService"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def availability_service(self, mock_db):
        """AvailabilityService instance with mocked database"""
        return AvailabilityService(mock_db)

    @pytest.fixture
    def sample_create_request(self):
        """Sample CreateAvailabilityRequest"""
        return CreateAvailabilityRequest(
            date=date(2024, 2, 15),
            start_time="09:00",
            end_time="17:00",
            timezone="America/New_York",
            slot_duration=30,
            appointment_type=AppointmentType.CONSULTATION,
            location=LocationSchema(
                type=LocationType.CLINIC,
                address="123 Medical Center Dr",
                room_number="Room 205",
            ),
            pricing=PricingSchema(
                base_fee=Decimal("150.00"), insurance_accepted=True, currency="USD"
            ),
        )

    def test_create_single_availability_success(
        self, availability_service, sample_create_request, mock_db
    ):
        """Test successful creation of single availability"""
        # Mock the database operations
        mock_availability = Mock(spec=ProviderAvailabilitySQL)
        mock_availability.id = "test-availability-id"
        mock_availability.provider_id = "test-provider-id"
        mock_availability.date = sample_create_request.date
        mock_availability.start_time = time(9, 0)
        mock_availability.end_time = time(17, 0)
        mock_availability.timezone = "America/New_York"
        mock_availability.slot_duration = 30
        mock_availability.break_duration = 0
        mock_availability.appointment_type = AppointmentType.CONSULTATION

        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # Mock conflict check to return no conflicts
        with patch.object(
            availability_service, "_find_conflicting_slots", return_value=[]
        ):
            with patch.object(
                availability_service, "_generate_appointment_slots", return_value=16
            ):
                result = availability_service._create_single_availability(
                    "test-provider-id", sample_create_request
                )

        assert result[0] == 16  # slots_created
        assert result[1] == "test-availability-id"  # availability_id
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_availability_with_conflicts(
        self, availability_service, sample_create_request
    ):
        """Test creating availability with conflicting slots"""
        # Mock conflict check to return conflicts
        with patch.object(
            availability_service,
            "_find_conflicting_slots",
            return_value=[{"id": "conflict-1"}],
        ):
            with pytest.raises(ValueError, match="Conflicting slots found"):
                availability_service.create_availability_slots(
                    "test-provider-id", sample_create_request
                )

    def test_should_create_slot_for_date_daily(self, availability_service):
        """Test daily recurrence pattern"""
        start_date = date(2024, 2, 15)  # Thursday
        current_date = date(2024, 2, 16)  # Friday

        result = availability_service._should_create_slot_for_date(
            current_date, start_date, RecurrencePattern.DAILY
        )
        assert result is True

    def test_should_create_slot_for_date_weekly(self, availability_service):
        """Test weekly recurrence pattern"""
        start_date = date(2024, 2, 15)  # Thursday
        next_week = date(2024, 2, 22)  # Next Thursday
        different_day = date(2024, 2, 16)  # Friday

        # Same weekday should return True
        result1 = availability_service._should_create_slot_for_date(
            next_week, start_date, RecurrencePattern.WEEKLY
        )
        assert result1 is True

        # Different weekday should return False
        result2 = availability_service._should_create_slot_for_date(
            different_day, start_date, RecurrencePattern.WEEKLY
        )
        assert result2 is False

    def test_add_minutes_to_time(self, availability_service):
        """Test adding minutes to time"""
        test_time = time(9, 30)
        result = availability_service._add_minutes_to_time(test_time, 45)
        assert result == time(10, 15)

    def test_combine_date_time(self, availability_service):
        """Test combining date and time with timezone"""
        test_date = date(2024, 2, 15)
        test_time = time(9, 0)
        result = availability_service._combine_date_time(
            test_date, test_time, "America/New_York"
        )

        assert isinstance(result, datetime)
        assert result.date() == test_date
        assert result.time() == test_time
        assert result.tzinfo is not None


class TestTimezoneHandling:
    """Test cases for timezone handling"""

    def test_timezone_conversion_utc_to_local(self):
        """Test converting UTC time to local timezone"""
        utc_time = datetime(2024, 2, 15, 14, 0, 0, tzinfo=pytz.UTC)
        ny_tz = pytz.timezone("America/New_York")
        local_time = utc_time.astimezone(ny_tz)

        # Should be 9 AM in New York (EST/EDT depending on daylight saving)
        assert local_time.hour in [8, 9, 10]  # Account for DST

    def test_daylight_saving_time_transition(self):
        """Test daylight saving time transition handling"""
        ny_tz = pytz.timezone("America/New_York")

        # Before DST
        before_dst = ny_tz.localize(datetime(2024, 3, 9, 2, 0, 0))
        # After DST
        after_dst = ny_tz.localize(datetime(2024, 3, 10, 2, 0, 0))

        # The time difference should be 23 hours due to spring forward
        time_diff = after_dst - before_dst
        assert time_diff.total_seconds() == 23 * 3600


class TestConflictDetection:
    """Test cases for conflict detection"""

    def test_overlapping_slots_detection(self):
        """Test detection of overlapping time slots"""
        # Slot 1: 9:00-10:00
        slot1_start = time(9, 0)
        slot1_end = time(10, 0)

        # Slot 2: 9:30-10:30 (overlaps)
        slot2_start = time(9, 30)
        slot2_end = time(10, 30)

        # Check for overlap
        has_overlap = slot1_start < slot2_end and slot1_end > slot2_start

        assert has_overlap is True

    def test_non_overlapping_slots(self):
        """Test that non-overlapping slots are not detected as conflicts"""
        # Slot 1: 9:00-10:00
        slot1_start = time(9, 0)
        slot1_end = time(10, 0)

        # Slot 2: 10:00-11:00 (adjacent, no overlap)
        slot2_start = time(10, 0)
        slot2_end = time(11, 0)

        # Check for overlap
        has_overlap = slot1_start < slot2_end and slot1_end > slot2_start

        assert has_overlap is False


class TestRecurrencePatterns:
    """Test cases for recurrence pattern handling"""

    def test_daily_recurrence_generation(self):
        """Test generating daily recurring dates"""
        start_date = date(2024, 2, 15)
        end_date = date(2024, 2, 18)

        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)

        expected_dates = [
            date(2024, 2, 15),
            date(2024, 2, 16),
            date(2024, 2, 17),
            date(2024, 2, 18),
        ]

        assert dates == expected_dates

    def test_weekly_recurrence_generation(self):
        """Test generating weekly recurring dates"""
        start_date = date(2024, 2, 15)  # Thursday
        end_date = date(2024, 3, 7)  # 3 weeks later

        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(weeks=1)

        expected_dates = [
            date(2024, 2, 15),  # Thursday
            date(2024, 2, 22),  # Next Thursday
            date(2024, 2, 29),  # Next Thursday
            date(2024, 3, 7),  # Next Thursday
        ]

        assert dates == expected_dates


if __name__ == "__main__":
    pytest.main([__file__])
