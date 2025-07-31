#!/usr/bin/env python3
"""
Example script demonstrating the Provider Availability Management module.

This script shows how to:
1. Create availability slots for a provider
2. Search for available slots
3. Handle timezone conversions
4. Work with recurring availability
"""

import sys
import os
from datetime import datetime, date, time
from decimal import Decimal

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.availability_schema import (
    CreateAvailabilityRequest,
    LocationSchema,
    PricingSchema,
    AvailabilitySearchRequest,
)
from app.models.availability_model import (
    AppointmentType,
    LocationType,
    RecurrencePattern,
)
from app.utils.timezone_utils import TimezoneUtils


def example_single_availability():
    """Example: Create single availability slots"""
    print("=== Single Availability Example ===")

    # Create a single availability request
    request = CreateAvailabilityRequest(
        date="2024-02-15",
        start_time="09:00",
        end_time="17:00",
        timezone="America/New_York",
        slot_duration=30,
        break_duration=15,
        appointment_type=AppointmentType.CONSULTATION,
        location=LocationSchema(
            type=LocationType.CLINIC,
            address="123 Medical Center Dr, New York, NY 10001",
            room_number="Room 205",
        ),
        pricing=PricingSchema(
            base_fee=Decimal("150.00"), insurance_accepted=True, currency="USD"
        ),
        special_requirements=["bring_insurance_card"],
        notes="Standard consultation slots",
    )

    print(f"Created availability request for {request.date}")
    print(f"Time: {request.start_time} - {request.end_time}")
    print(f"Timezone: {request.timezone}")
    print(f"Slot duration: {request.slot_duration} minutes")
    print(f"Location: {request.location.address}")
    print(f"Pricing: ${request.pricing.base_fee}")
    print()


def example_recurring_availability():
    """Example: Create recurring availability slots"""
    print("=== Recurring Availability Example ===")

    # Create a weekly recurring availability request
    request = CreateAvailabilityRequest(
        date="2024-02-15",  # Thursday
        start_time="09:00",
        end_time="17:00",
        timezone="America/New_York",
        slot_duration=30,
        break_duration=15,
        is_recurring=True,
        recurrence_pattern=RecurrencePattern.WEEKLY,
        recurrence_end_date="2024-08-15",
        appointment_type=AppointmentType.CONSULTATION,
        location=LocationSchema(
            type=LocationType.CLINIC,
            address="123 Medical Center Dr, New York, NY 10001",
            room_number="Room 205",
        ),
        pricing=PricingSchema(
            base_fee=Decimal("150.00"), insurance_accepted=True, currency="USD"
        ),
        notes="Weekly consultation slots",
    )

    print(f"Created recurring availability request")
    print(f"Pattern: {request.recurrence_pattern}")
    print(f"Start date: {request.date}")
    print(f"End date: {request.recurrence_end_date}")
    print(
        f"Will create slots every {request.recurrence_pattern} until {request.recurrence_end_date}"
    )
    print()


def example_timezone_handling():
    """Example: Timezone handling and conversions"""
    print("=== Timezone Handling Example ===")

    # Validate timezone
    timezone = "America/New_York"
    is_valid = TimezoneUtils.validate_timezone(timezone)
    print(f"Timezone '{timezone}' is valid: {is_valid}")

    # Get timezone offset
    offset_seconds = TimezoneUtils.get_timezone_offset(timezone)
    offset_hours = offset_seconds / 3600
    print(f"Current offset for {timezone}: {offset_hours} hours from UTC")

    # Combine date and time with timezone
    test_date = date(2024, 2, 15)
    test_time = time(9, 0)
    dt = TimezoneUtils.combine_date_time_with_timezone(test_date, test_time, timezone)
    print(f"Combined datetime: {dt}")
    print(f"Timezone info: {dt.tzinfo}")

    # Convert to different timezone
    utc_dt = TimezoneUtils.get_utc_from_local_time(dt, timezone)
    print(f"UTC equivalent: {utc_dt}")

    # Convert back to local time
    local_dt = TimezoneUtils.get_local_time_from_utc(utc_dt, timezone)
    print(f"Local time: {local_dt}")
    print()


def example_search_request():
    """Example: Create search request for available slots"""
    print("=== Search Request Example ===")

    # Create a search request
    search_request = AvailabilitySearchRequest(
        date="2024-02-15",
        specialization="cardiology",
        location="New York, NY",
        appointment_type=AppointmentType.CONSULTATION,
        insurance_accepted=True,
        max_price=Decimal("200.00"),
        timezone="America/New_York",
        available_only=True,
    )

    print(f"Search request created")
    print(f"Date: {search_request.date}")
    print(f"Specialization: {search_request.specialization}")
    print(f"Location: {search_request.location}")
    print(f"Appointment type: {search_request.appointment_type}")
    print(f"Insurance accepted: {search_request.insurance_accepted}")
    print(f"Max price: ${search_request.max_price}")
    print(f"Timezone: {search_request.timezone}")
    print()


def example_time_validation():
    """Example: Time validation and manipulation"""
    print("=== Time Validation Example ===")

    # Test time range validation
    start_time = time(9, 0)
    end_time = time(17, 0)

    is_valid, error = TimezoneUtils.validate_time_range(
        start_time, end_time, min_duration_minutes=15, max_duration_hours=24
    )

    print(f"Time range {start_time} - {end_time} is valid: {is_valid}")
    if not is_valid:
        print(f"Error: {error}")

    # Test invalid time range
    invalid_start = time(17, 0)
    invalid_end = time(9, 0)

    is_valid, error = TimezoneUtils.validate_time_range(invalid_start, invalid_end)
    print(f"Time range {invalid_start} - {invalid_end} is valid: {is_valid}")
    if not is_valid:
        print(f"Error: {error}")

    # Test adding minutes to time
    original_time = time(9, 30)
    new_time = TimezoneUtils.add_minutes_to_time(original_time, 45)
    print(f"Adding 45 minutes to {original_time}: {new_time}")

    # Test time difference
    time1 = time(9, 0)
    time2 = time(10, 30)
    diff_minutes = TimezoneUtils.get_time_difference_minutes(time1, time2)
    print(f"Difference between {time1} and {time2}: {diff_minutes} minutes")
    print()


def example_common_timezones():
    """Example: List common timezones"""
    print("=== Common Timezones Example ===")

    common_timezones = TimezoneUtils.get_common_timezones()
    print("Common timezones supported:")
    for tz in common_timezones:
        print(f"  - {tz}")
    print()


def main():
    """Run all examples"""
    print("Provider Availability Management Module Examples")
    print("=" * 50)
    print()

    try:
        example_single_availability()
        example_recurring_availability()
        example_timezone_handling()
        example_search_request()
        example_time_validation()
        example_common_timezones()

        print("All examples completed successfully!")

    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
