import pytz
from datetime import datetime, date, time
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


class TimezoneUtils:
    """Utility class for timezone handling and time conversions"""

    @staticmethod
    def validate_timezone(timezone_str: str) -> bool:
        """
        Validate if a timezone string is valid.

        Args:
            timezone_str: Timezone string (e.g., "America/New_York")

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            pytz.timezone(timezone_str)
            return True
        except pytz.exceptions.UnknownTimeZoneError:
            return False

    @staticmethod
    def get_timezone_offset(timezone_str: str, dt: Optional[datetime] = None) -> int:
        """
        Get the UTC offset in seconds for a timezone at a specific datetime.

        Args:
            timezone_str: Timezone string
            dt: Datetime to get offset for (defaults to current time)

        Returns:
            int: UTC offset in seconds
        """
        if dt is None:
            dt = datetime.now()

        tz = pytz.timezone(timezone_str)
        offset = tz.utcoffset(dt)
        return int(offset.total_seconds())

    @staticmethod
    def convert_datetime_to_timezone(
        dt: datetime, from_timezone: str, to_timezone: str
    ) -> datetime:
        """
        Convert a datetime from one timezone to another.

        Args:
            dt: Datetime to convert
            from_timezone: Source timezone
            to_timezone: Target timezone

        Returns:
            datetime: Converted datetime in target timezone
        """
        if dt.tzinfo is None:
            # If datetime is naive, assume it's in from_timezone
            from_tz = pytz.timezone(from_timezone)
            dt = from_tz.localize(dt)

        to_tz = pytz.timezone(to_timezone)
        return dt.astimezone(to_tz)

    @staticmethod
    def combine_date_time_with_timezone(
        d: date, t: time, timezone_str: str
    ) -> datetime:
        """
        Combine date and time into a timezone-aware datetime.

        Args:
            d: Date
            t: Time
            timezone_str: Timezone string

        Returns:
            datetime: Timezone-aware datetime
        """
        naive_dt = datetime.combine(d, t)
        tz = pytz.timezone(timezone_str)
        return tz.localize(naive_dt)

    @staticmethod
    def get_local_time_from_utc(utc_dt: datetime, timezone_str: str) -> datetime:
        """
        Convert UTC datetime to local time in specified timezone.

        Args:
            utc_dt: UTC datetime
            timezone_str: Target timezone

        Returns:
            datetime: Local datetime in target timezone
        """
        if utc_dt.tzinfo is None:
            # Assume UTC if no timezone info
            utc_dt = pytz.UTC.localize(utc_dt)

        target_tz = pytz.timezone(timezone_str)
        return utc_dt.astimezone(target_tz)

    @staticmethod
    def get_utc_from_local_time(local_dt: datetime, timezone_str: str) -> datetime:
        """
        Convert local datetime to UTC.

        Args:
            local_dt: Local datetime
            timezone_str: Source timezone

        Returns:
            datetime: UTC datetime
        """
        if local_dt.tzinfo is None:
            # If naive, assume it's in the specified timezone
            source_tz = pytz.timezone(timezone_str)
            local_dt = source_tz.localize(local_dt)

        return local_dt.astimezone(pytz.UTC)

    @staticmethod
    def is_dst_transition_date(dt: datetime, timezone_str: str) -> bool:
        """
        Check if a date is a daylight saving time transition date.

        Args:
            dt: Date to check
            timezone_str: Timezone string

        Returns:
            bool: True if it's a DST transition date
        """
        tz = pytz.timezone(timezone_str)

        # Check if the date is a DST transition date
        try:
            # Get the transition times for the year
            transitions = tz._utc_transition_times

            # Check if any transition occurs on this date
            for transition in transitions:
                if transition.date() == dt.date():
                    return True

            return False
        except AttributeError:
            # Some timezones don't have transition data
            return False

    @staticmethod
    def get_business_hours_in_timezone(
        start_time: time, end_time: time, timezone_str: str, target_timezone: str
    ) -> tuple[time, time]:
        """
        Convert business hours from one timezone to another.

        Args:
            start_time: Start time in source timezone
            end_time: End time in source timezone
            timezone_str: Source timezone
            target_timezone: Target timezone

        Returns:
            tuple: (start_time, end_time) in target timezone
        """
        # Create a reference date (today)
        ref_date = date.today()

        # Combine with times and localize
        source_tz = pytz.timezone(timezone_str)
        start_dt = source_tz.localize(datetime.combine(ref_date, start_time))
        end_dt = source_tz.localize(datetime.combine(ref_date, end_time))

        # Convert to target timezone
        target_tz = pytz.timezone(target_timezone)
        start_dt_target = start_dt.astimezone(target_tz)
        end_dt_target = end_dt.astimezone(target_tz)

        return start_dt_target.time(), end_dt_target.time()

    @staticmethod
    def format_time_for_timezone(
        dt: datetime, timezone_str: str, format_str: str = "%H:%M"
    ) -> str:
        """
        Format a datetime for a specific timezone.

        Args:
            dt: Datetime to format
            timezone_str: Target timezone
            format_str: Format string

        Returns:
            str: Formatted time string
        """
        if dt.tzinfo is None:
            # Assume UTC if no timezone info
            dt = pytz.UTC.localize(dt)

        target_tz = pytz.timezone(timezone_str)
        local_dt = dt.astimezone(target_tz)
        return local_dt.strftime(format_str)

    @staticmethod
    def get_common_timezones() -> list[str]:
        """
        Get a list of common timezones.

        Returns:
            list: List of common timezone strings
        """
        return [
            "UTC",
            "America/New_York",
            "America/Chicago",
            "America/Denver",
            "America/Los_Angeles",
            "America/Anchorage",
            "America/Honolulu",
            "Europe/London",
            "Europe/Paris",
            "Europe/Berlin",
            "Europe/Moscow",
            "Asia/Tokyo",
            "Asia/Shanghai",
            "Asia/Kolkata",
            "Australia/Sydney",
            "Australia/Perth",
            "Pacific/Auckland",
        ]

    @staticmethod
    def validate_time_range(
        start_time: time,
        end_time: time,
        min_duration_minutes: int = 15,
        max_duration_hours: int = 24,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a time range.

        Args:
            start_time: Start time
            end_time: End time
            min_duration_minutes: Minimum duration in minutes
            max_duration_hours: Maximum duration in hours

        Returns:
            tuple: (is_valid, error_message)
        """
        if end_time <= start_time:
            return False, "End time must be after start time"

        # Calculate duration
        start_minutes = start_time.hour * 60 + start_time.minute
        end_minutes = end_time.hour * 60 + end_time.minute
        duration_minutes = end_minutes - start_minutes

        if duration_minutes < min_duration_minutes:
            return False, f"Duration must be at least {min_duration_minutes} minutes"

        if duration_minutes > max_duration_hours * 60:
            return False, f"Duration must not exceed {max_duration_hours} hours"

        return True, None

    @staticmethod
    def add_minutes_to_time(t: time, minutes: int) -> time:
        """
        Add minutes to a time object.

        Args:
            t: Time object
            minutes: Minutes to add

        Returns:
            time: New time object
        """
        total_minutes = t.hour * 60 + t.minute + minutes
        hours = total_minutes // 60
        mins = total_minutes % 60
        return time(hour=hours, minute=mins)

    @staticmethod
    def subtract_minutes_from_time(t: time, minutes: int) -> time:
        """
        Subtract minutes from a time object.

        Args:
            t: Time object
            minutes: Minutes to subtract

        Returns:
            time: New time object
        """
        total_minutes = t.hour * 60 + t.minute - minutes
        if total_minutes < 0:
            total_minutes += 24 * 60  # Add 24 hours

        hours = total_minutes // 60
        mins = total_minutes % 60
        return time(hour=hours, minute=mins)

    @staticmethod
    def get_time_difference_minutes(start_time: time, end_time: time) -> int:
        """
        Get the difference between two times in minutes.

        Args:
            start_time: Start time
            end_time: End time

        Returns:
            int: Difference in minutes
        """
        start_minutes = start_time.hour * 60 + start_time.minute
        end_minutes = end_time.hour * 60 + end_time.minute

        if end_minutes < start_minutes:
            # End time is on the next day
            end_minutes += 24 * 60

        return end_minutes - start_minutes
