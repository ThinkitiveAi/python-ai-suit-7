# Provider Registration Backend

A secure and comprehensive backend module for healthcare provider registration with email verification, built with FastAPI.

## Features

- **Secure Authentication**: Password hashing with bcrypt (12 salt rounds)
- **Comprehensive Validation**: Input sanitization, format validation, and duplicate checking
- **Email Verification**: JWT-based email verification with secure tokens
- **Rate Limiting**: Redis-based rate limiting (5 attempts per hour per IP)
- **Multi-Database Support**: Works with PostgreSQL, MySQL, or MongoDB
- **Audit Logging**: Comprehensive logging for monitoring and debugging
- **RESTful API**: Clean, well-documented REST endpoints
- **Testing**: Comprehensive unit and integration tests

## Project Structure

```
app/
├── controllers/
│   └── provider_controller.py      # HTTP request handlers
├── services/
│   ├── provider_service.py         # Business logic
│   ├── email_service.py           # Email operations
│   └── validation_service.py      # Data validation
├── models/
│   └── provider.py                # Database models
├── middlewares/
│   ├── validation.py              # Input sanitization
│   └── rate_limiting.py           # Rate limiting
├── utils/
│   ├── password_utils.py          # Password operations
│   └── email_utils.py             # Email utilities
├── schemas/
│   └── provider_schema.py         # Pydantic schemas
├── core/
│   ├── config.py                  # Configuration
│   └── database.py                # Database setup
└── main.py                        # FastAPI application
tests/
└── test_provider_registration.py  # Test suite
```

## Database Schema

### Provider Schema
- `id` (UUID/ObjectId): Unique identifier
- `first_name` (string, 2-50 chars): Provider's first name
- `last_name` (string, 2-50 chars): Provider's last name
- `email` (string, unique): Valid email address
- `phone_number` (string, unique): International phone format
- `password_hash` (string): Bcrypt hashed password
- `specialization` (string, 3-100 chars): Medical specialization
- `license_number` (string, unique): Alphanumeric license number
- `years_of_experience` (integer, 0-50): Years of experience
- `clinic_address` (object): Street, city, state, zip
- `verification_status` (enum): pending/verified/rejected
- `license_document_url` (string, optional): Document URL
- `is_active` (boolean): Account status
- `created_at` (timestamp): Creation time
- `updated_at` (timestamp): Last update time

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd provider_registration_backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Configure database**
   - For PostgreSQL/MySQL: Set `DATABASE_URL`
   - For MongoDB: Set `MONGODB_URL` and `MONGODB_DATABASE`
   - Set `DATABASE_TYPE` to "postgresql", "mysql", or "mongodb"

6. **Set up Redis** (for rate limiting)
   ```bash
   # Install Redis or use Docker
   docker run -d -p 6379:6379 redis:alpine
   ```

## Configuration

Create a `.env` file with the following variables:

```env
# Application
APP_NAME=Provider Registration API
APP_VERSION=1.0.0
DEBUG=false

# Database
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:password@localhost/provider_registration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=provider_registration

# Security
SECRET_KEY=your-secret-key-change-in-production
BCRYPT_ROUNDS=12

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@provider-registration.com

# Redis
REDIS_URL=redis://localhost:6379

# Rate Limiting
RATE_LIMIT_REQUESTS=5
RATE_LIMIT_WINDOW=3600

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

## API Endpoints

### 1. Provider Registration
**POST** `/api/v1/provider/register`

Register a new healthcare provider.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@clinic.com",
  "phone_number": "+1234567890",
  "password": "SecurePassword123!",
  "confirm_password": "SecurePassword123!",
  "specialization": "Cardiology",
  "license_number": "MD123456789",
  "years_of_experience": 10,
  "clinic_address": {
    "street": "123 Medical Center Dr",
    "city": "New York",
    "state": "NY",
    "zip": "10001"
  }
}
```

**Success Response (201):**
```json
{
  "success": true,
  "message": "Provider registered successfully. Verification email sent.",
  "data": {
    "provider_id": "uuid-here",
    "email": "john.doe@clinic.com",
    "verification_status": "pending"
  }
}
```

### 2. Email Verification
**GET** `/api/v1/provider/verify?token=<verification_token>`

Verify provider email address.

**Success Response (200):**
```json
{
  "success": true,
  "message": "Email verified successfully. Welcome!",
  "data": {
    "provider_id": "uuid-here",
    "email": "john.doe@clinic.com",
    "verification_status": "verified"
  }
}
```

### 3. Get Provider Details
**GET** `/api/v1/provider/{provider_id}`

Get provider details by ID.

### 4. Health Check
**GET** `/health`

Check API health status.

## Validation Rules

### Email
- Must be unique
- Valid email format
- No disposable email domains

### Phone Number
- Must be unique
- International format (e.g., +1234567890)

### Password
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

### License Number
- Must be unique
- Alphanumeric only
- Minimum 5 characters

### Specialization
Must be one of:
- Cardiology, Dermatology, Endocrinology, Gastroenterology
- General Practice, Internal Medicine, Neurology, Oncology
- Orthopedics, Pediatrics, Psychiatry, Radiology
- Surgery, Urology, Obstetrics and Gynecology, Emergency Medicine
- Family Medicine, Anesthesiology, Pathology, Ophthalmology

## Security Features

- **Password Hashing**: Bcrypt with 12 salt rounds
- **Input Sanitization**: XSS and injection attack prevention
- **Rate Limiting**: 5 registration attempts per IP per hour
- **Email Verification**: Required before account activation
- **JWT Tokens**: Secure email verification tokens
- **CORS Protection**: Configurable CORS settings
- **Audit Logging**: Comprehensive security event logging

## Running the Application

### Development
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Docker
```bash
# Build image
docker build -t provider-registration-api .

# Run container
docker run -p 8000:8000 provider-registration-api
```

## Testing

### Run all tests
```bash
pytest tests/
```

### Run with coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_provider_registration.py -v
```

## API Documentation

Once the application is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Error Handling

The API returns appropriate HTTP status codes:

- **200**: Success
- **201**: Created (registration successful)
- **400**: Bad Request (validation errors)
- **409**: Conflict (duplicate data)
- **422**: Unprocessable Entity (validation errors)
- **429**: Too Many Requests (rate limited)
- **500**: Internal Server Error

## Logging

Logs are written to both console and file:
- **Console**: Colored output for development
- **File**: `logs/app.log` with rotation (10MB, 30 days retention)

## Monitoring

The application includes:
- Request timing headers (`X-Process-Time`)
- Rate limit headers (`X-RateLimit-*`)
- Health check endpoints
- Comprehensive error logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the API documentation at `/docs` 