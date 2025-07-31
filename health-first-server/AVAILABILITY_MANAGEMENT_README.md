# Provider Availability Management Module

A comprehensive module for managing healthcare provider availability, appointment slots, and patient search functionality.

## Features

- **Provider Availability Management**: Create, update, and delete availability slots
- **Recurring Availability**: Support for daily, weekly, and monthly recurring patterns
- **Timezone Handling**: Full timezone support with daylight saving time transitions
- **Conflict Detection**: Prevent overlapping availability slots
- **Patient Search**: Search for available appointment slots across providers
- **Multi-database Support**: Works with both SQL (PostgreSQL/MySQL) and NoSQL (MongoDB) databases
- **Comprehensive Validation**: Input validation and business rule enforcement

## Database Schema

### Provider Availability Schema

```sql
CREATE TABLE provider_availability (
    id UUID PRIMARY KEY,
    provider_id UUID NOT NULL REFERENCES providers(id),
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_pattern ENUM('daily', 'weekly', 'monthly'),
    recurrence_end_date DATE,
    slot_duration INTEGER DEFAULT 30,
    break_duration INTEGER DEFAULT 0,
    status ENUM('available', 'booked', 'cancelled', 'blocked', 'maintenance') DEFAULT 'available',
    max_appointments_per_slot INTEGER DEFAULT 1,
    current_appointments INTEGER DEFAULT 0,
    appointment_type ENUM('consultation', 'follow_up', 'emergency', 'telemedicine') DEFAULT 'consultation',
    location JSON,
    pricing JSON,
    notes TEXT,
    special_requirements JSON DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### Appointment Slots Schema

```sql
CREATE TABLE appointment_slots (
    id UUID PRIMARY KEY,
    availability_id UUID NOT NULL REFERENCES provider_availability(id),
    provider_id UUID NOT NULL REFERENCES providers(id),
    slot_start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    slot_end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status ENUM('available', 'booked', 'cancelled', 'blocked') DEFAULT 'available',
    patient_id UUID REFERENCES patients(id),
    appointment_type VARCHAR(50) NOT NULL,
    booking_reference VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## API Endpoints

### 1. Create Availability Slots

**POST** `/api/v1/provider/availability`

Create availability slots for a healthcare provider.

**Request Body:**
```json
{
  "date": "2024-02-15",
  "start_time": "09:00",
  "end_time": "17:00",
  "timezone": "America/New_York",
  "slot_duration": 30,
  "break_duration": 15,
  "is_recurring": true,
  "recurrence_pattern": "weekly",
  "recurrence_end_date": "2024-08-15",
  "appointment_type": "consultation",
  "location": {
    "type": "clinic",
    "address": "123 Medical Center Dr, New York, NY 10001",
    "room_number": "Room 205"
  },
  "pricing": {
    "base_fee": 150.00,
    "insurance_accepted": true,
    "currency": "USD"
  },
  "special_requirements": ["fasting_required", "bring_insurance_card"],
  "notes": "Standard consultation slots"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Availability slots created successfully",
  "data": {
    "availability_id": "uuid-here",
    "slots_created": 32,
    "date_range": {
      "start": "2024-02-15",
      "end": "2024-08-15"
    },
    "total_appointments_available": 224
  }
}
```

### 2. Get Provider Availability

**GET** `/api/v1/provider/{provider_id}/availability`

Retrieve availability information for a specific provider.

**Query Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)
- `status` (optional): Filter by slot status
- `appointment_type` (optional): Filter by appointment type
- `timezone` (optional): Timezone for time conversion

**Response:**
```json
{
  "provider_id": "uuid-here",
  "availability_summary": {
    "total_slots": 48,
    "available_slots": 32,
    "booked_slots": 14,
    "cancelled_slots": 2
  },
  "availability": [
    {
      "date": "2024-02-15",
      "slots": [
        {
          "slot_id": "uuid-here",
          "start_time": "09:00",
          "end_time": "09:30",
          "status": "available",
          "appointment_type": "consultation",
          "location": {
            "type": "clinic",
            "address": "123 Medical Center Dr",
            "room_number": "Room 205"
          },
          "pricing": {
            "base_fee": 150.00,
            "insurance_accepted": true
          }
        }
      ]
    }
  ]
}
```

### 3. Update Availability Slot

**PUT** `/api/v1/provider/availability/{slot_id}`

Update a specific availability slot.

**Request Body:**
```json
{
  "start_time": "10:00",
  "end_time": "10:30",
  "status": "available",
  "notes": "Updated consultation time",
  "pricing": {
    "base_fee": 175.00
  }
}
```

### 4. Delete Availability Slot

**DELETE** `/api/v1/provider/availability/{slot_id}`

Delete a specific availability slot.

**Query Parameters:**
- `delete_recurring` (optional): Delete all recurring instances
- `reason` (optional): Reason for deletion

### 5. Search Available Slots

**GET** `/api/v1/availability/search`

Search for available appointment slots across providers.

**Query Parameters:**
- `date` (optional): Specific date to search
- `start_date` & `end_date` (optional): Date range
- `specialization` (optional): Medical specialization
- `location` (optional): Location (city, state, or zip)
- `appointment_type` (optional): Appointment type
- `insurance_accepted` (optional): Whether insurance is accepted
- `max_price` (optional): Maximum price
- `timezone` (optional): Timezone for time conversion
- `available_only` (default: true): Show only available slots

**Response:**
```json
{
  "success": true,
  "data": {
    "search_criteria": {
      "date": "2024-02-15",
      "specialization": "cardiology",
      "location": "New York, NY"
    },
    "total_results": 15,
    "results": [
      {
        "provider": {
          "id": "uuid-here",
          "name": "Dr. John Doe",
          "specialization": "Cardiology",
          "years_of_experience": 15,
          "rating": 4.8,
          "clinic_address": "123 Medical Center Dr, New York, NY"
        },
        "available_slots": [
          {
            "slot_id": "uuid-here",
            "date": "2024-02-15",
            "start_time": "10:00",
            "end_time": "10:30",
            "appointment_type": "consultation",
            "location": {
              "type": "clinic",
              "address": "123 Medical Center Dr",
              "room_number": "Room 205"
            },
            "pricing": {
              "base_fee": 150.00,
              "insurance_accepted": true,
              "currency": "USD"
            },
            "special_requirements": ["bring_insurance_card"]
          }
        ]
      }
    ]
  }
}
```

### 6. Get Availability Summary

**GET** `/api/v1/provider/availability/summary`

Get a summary of provider's availability statistics.

**Query Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)

### 7. Bulk Update Availability

**POST** `/api/v1/provider/availability/bulk-update`

Update multiple availability slots at once.

**Request Body:**
```json
{
  "slot_ids": ["uuid1", "uuid2", "uuid3"],
  "request": {
    "status": "blocked",
    "notes": "Holiday closure"
  }
}
```

### 8. Check for Conflicts

**GET** `/api/v1/provider/availability/conflicts`

Check for scheduling conflicts in provider's availability.

**Query Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)

## Usage Examples

### Creating Single Availability

```python
from app.services.availability_service import AvailabilityService
from app.schemas.availability_schema import CreateAvailabilityRequest, LocationSchema, PricingSchema
from decimal import Decimal

# Create availability service
service = AvailabilityService(db)

# Create request
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
        room_number="Room 205"
    ),
    pricing=PricingSchema(
        base_fee=Decimal("150.00"),
        insurance_accepted=True,
        currency="USD"
    )
)

# Create availability slots
result = service.create_availability_slots("provider-id", request)
print(f"Created {result['slots_created']} slots")
```

### Creating Recurring Availability

```python
# Create weekly recurring availability
request = CreateAvailabilityRequest(
    date=date(2024, 2, 15),
    start_time="09:00",
    end_time="17:00",
    timezone="America/New_York",
    is_recurring=True,
    recurrence_pattern=RecurrencePattern.WEEKLY,
    recurrence_end_date=date(2024, 8, 15),
    slot_duration=30,
    appointment_type=AppointmentType.CONSULTATION,
    location=LocationSchema(
        type=LocationType.CLINIC,
        address="123 Medical Center Dr"
    )
)

result = service.create_availability_slots("provider-id", request)
```

### Searching for Available Slots

```python
from app.schemas.availability_schema import AvailabilitySearchRequest

# Create search request
search_request = AvailabilitySearchRequest(
    date=date(2024, 2, 15),
    specialization="cardiology",
    location="New York, NY",
    appointment_type=AppointmentType.CONSULTATION,
    insurance_accepted=True,
    max_price=Decimal("200.00")
)

# Search for available slots
results = service.search_available_slots(search_request)
print(f"Found {results['total_results']} providers with available slots")
```

## Timezone Handling

The module includes comprehensive timezone support:

### Timezone Utilities

```python
from app.utils.timezone_utils import TimezoneUtils

# Validate timezone
is_valid = TimezoneUtils.validate_timezone("America/New_York")

# Convert datetime between timezones
utc_time = datetime(2024, 2, 15, 14, 0, 0, tzinfo=pytz.UTC)
local_time = TimezoneUtils.get_local_time_from_utc(utc_time, "America/New_York")

# Combine date and time with timezone
dt = TimezoneUtils.combine_date_time_with_timezone(
    date(2024, 2, 15), 
    time(9, 0), 
    "America/New_York"
)

# Check for DST transitions
is_dst = TimezoneUtils.is_dst_transition_date(dt, "America/New_York")
```

### Common Timezones

The module supports all standard timezones including:
- UTC
- America/New_York
- America/Chicago
- America/Denver
- America/Los_Angeles
- Europe/London
- Europe/Paris
- Asia/Tokyo
- And many more...

## Validation Rules

### Time Validation
- End time must be after start time
- Minimum slot duration: 15 minutes
- Maximum slot duration: 24 hours
- Time format: HH:mm (24-hour)

### Recurrence Validation
- Recurrence pattern required for recurring availability
- Recurrence end date must be after start date
- Supported patterns: daily, weekly, monthly

### Location Validation
- Address required for physical locations (clinic, hospital, home_visit)
- Address optional for telemedicine

### Pricing Validation
- Base fee must be non-negative
- Currency must be valid ISO 4217 code

## Error Handling

The module includes comprehensive error handling:

### Common Error Responses

```json
{
  "success": false,
  "message": "Validation failed",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "start_time": ["Time must be in HH:mm format"],
    "end_time": ["End time must be after start time"]
  }
}
```

### Error Codes
- `VALIDATION_ERROR`: Input validation failed
- `CONFLICT_ERROR`: Scheduling conflict detected
- `NOT_FOUND`: Resource not found
- `UNAUTHORIZED`: Access denied
- `INTERNAL_ERROR`: Server error

## Testing

Run the test suite:

```bash
# Run all availability tests
pytest tests/test_availability.py -v

# Run specific test categories
pytest tests/test_availability.py::TestAvailabilityModels -v
pytest tests/test_availability.py::TestAvailabilitySchemas -v
pytest tests/test_availability.py::TestAvailabilityService -v
pytest tests/test_availability.py::TestTimezoneHandling -v
pytest tests/test_availability.py::TestConflictDetection -v
```

### Test Coverage

The test suite covers:
- Model creation and validation
- Schema validation and error handling
- Service business logic
- Timezone conversions and DST handling
- Conflict detection algorithms
- Recurrence pattern generation
- API endpoint functionality

## Configuration

### Environment Variables

```bash
# Database configuration
DATABASE_TYPE=postgresql  # or mysql, mongodb
DATABASE_URL=postgresql://user:password@localhost/dbname

# Timezone settings
DEFAULT_TIMEZONE=UTC
SUPPORTED_TIMEZONES=UTC,America/New_York,Europe/London

# Availability settings
MIN_SLOT_DURATION=15
MAX_SLOT_DURATION=1440  # 24 hours in minutes
DEFAULT_SLOT_DURATION=30
```

### Database Setup

For SQL databases, the tables will be created automatically when the application starts.

For MongoDB, the collections will be created automatically when first accessed.

## Security Considerations

- All endpoints require authentication
- Providers can only access their own availability data
- Input validation prevents injection attacks
- Timezone validation prevents timezone-related attacks
- Rate limiting prevents abuse

## Performance Considerations

- Database indexes on frequently queried fields
- Efficient timezone conversions
- Optimized conflict detection algorithms
- Pagination for large result sets
- Caching for timezone data

## Future Enhancements

- Calendar integration (Google Calendar, Outlook)
- SMS/Email notifications for availability changes
- Advanced recurrence patterns (custom intervals)
- Waitlist functionality
- Automated conflict resolution
- Analytics and reporting
- Mobile app support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This module is part of the Health First Server project and follows the same licensing terms. 