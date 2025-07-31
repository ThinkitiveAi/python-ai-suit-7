# Patient Registration Module

A comprehensive backend module for Patient Registration with secure authentication and comprehensive validation. This module supports both relational (MySQL/PostgreSQL) and NoSQL (MongoDB) database setups with HIPAA compliance considerations.

## Features

### 🔐 Security Features
- **Password Hashing**: bcrypt with configurable salt rounds (default: 12)
- **JWT Authentication**: Access and refresh tokens with proper expiration
- **Account Lockout**: Automatic account locking after failed login attempts
- **Input Validation**: Comprehensive validation for all user inputs
- **HIPAA Compliance**: Audit trails and secure data handling

### 📊 Database Support
- **Relational Databases**: PostgreSQL, MySQL with SQLAlchemy ORM
- **NoSQL Databases**: MongoDB with native driver support
- **Flexible Schema**: Works with both database types seamlessly

### ✅ Validation Rules
- **Email**: Unique, valid format, case-insensitive
- **Phone**: Unique, international format validation
- **Password**: 8+ characters, uppercase, lowercase, number, special character
- **Age**: Minimum 13 years for COPPA compliance
- **Address**: Valid postal code format
- **Medical Data**: Proper validation and sanitization

### 📧 Communication
- **Email Verification**: Automated verification emails
- **SMS Verification**: Phone number verification (placeholder implementation)
- **Welcome Emails**: Automated welcome messages

## Installation

### Prerequisites
- Python 3.8+
- FastAPI
- SQLAlchemy (for relational databases)
- PyMongo (for MongoDB)
- bcrypt
- PyJWT

### Dependencies
```bash
pip install fastapi sqlalchemy pymongo bcrypt pyjwt python-multipart
```

### Environment Configuration
Create a `.env` file with the following variables:

```env
# Database Configuration
DATABASE_TYPE=postgresql  # postgresql, mysql, or mongodb
DATABASE_URL=postgresql://user:password@localhost/health_first
MONGODB_URL=mongodb://localhost:27017/
MONGODB_DATABASE=health_first

# Security
SECRET_KEY=your-secret-key-change-in-production
BCRYPT_ROUNDS=12
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@health-first.com

# Rate Limiting
RATE_LIMIT_REQUESTS=5
RATE_LIMIT_WINDOW=3600
```

## API Endpoints

### Patient Registration

#### POST `/api/v1/patient/register`
Register a new patient account.

**Request Body:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane.smith@email.com",
  "phone_number": "+1234567890",
  "password": "SecurePassword123!",
  "confirm_password": "SecurePassword123!",
  "date_of_birth": "1990-05-15",
  "gender": "female",
  "address": {
    "street": "456 Main Street",
    "city": "Boston",
    "state": "MA",
    "zip": "02101"
  },
  "emergency_contact": {
    "name": "John Smith",
    "phone": "+1234567891",
    "relationship": "spouse"
  },
  "insurance_info": {
    "provider": "Blue Cross",
    "policy_number": "BC123456789"
  },
  "medical_history": ["Allergies to penicillin", "Previous surgery in 2018"]
}
```

**Success Response (201):**
```json
{
  "success": true,
  "message": "Patient registered successfully. Verification email sent.",
  "data": {
    "patient_id": "uuid-here",
    "email": "jane.smith@email.com",
    "phone_number": "+1234567890",
    "email_verified": false,
    "phone_verified": false
  }
}
```

**Validation Error Response (422):**
```json
{
  "success": false,
  "message": "Validation failed",
  "errors": {
    "email": ["Email is already registered"],
    "password": ["Password must contain at least 8 characters"],
    "date_of_birth": ["Must be at least 13 years old"]
  }
}
```

### Patient Authentication

#### POST `/api/v1/patient/login`
Authenticate patient login.

**Request Body:**
```json
{
  "identifier": "jane.smith@email.com",
  "password": "SecurePassword123!",
  "remember_me": false
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "patient": {
      "id": "uuid-here",
      "first_name": "Jane",
      "last_name": "Smith",
      "email": "jane.smith@email.com",
      "email_verified": false,
      "phone_verified": false
    }
  }
}
```

### Patient Profile Management

#### GET `/api/v1/patient/profile`
Get current patient's profile (requires authentication).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200):**
```json
{
  "id": "uuid-here",
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane.smith@email.com",
  "phone_number": "+1234567890",
  "date_of_birth": "1990-05-15",
  "gender": "female",
  "address": {
    "street": "456 Main Street",
    "city": "Boston",
    "state": "MA",
    "zip": "02101"
  },
  "emergency_contact": {
    "name": "John Smith",
    "phone": "+1234567891",
    "relationship": "spouse"
  },
  "medical_history": ["Allergies to penicillin", "Previous surgery in 2018"],
  "insurance_info": {
    "provider": "Blue Cross",
    "policy_number": "BC123456789"
  },
  "email_verified": false,
  "phone_verified": false,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### PUT `/api/v1/patient/profile`
Update patient profile (requires authentication).

**Request Body:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith-Jones",
  "phone_number": "+1234567890",
  "address": {
    "street": "789 New Street",
    "city": "New York",
    "state": "NY",
    "zip": "10001"
  }
}
```

### Patient Logout

#### POST `/api/v1/patient/logout`
Logout patient by revoking refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## Database Schema

### SQL Database Schema

#### Patients Table
```sql
CREATE TABLE patients (
    id VARCHAR(36) PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    date_of_birth DATE NOT NULL,
    gender ENUM('male', 'female', 'other', 'prefer_not_to_say') NOT NULL,
    address_street VARCHAR(200) NOT NULL,
    address_city VARCHAR(100) NOT NULL,
    address_state VARCHAR(50) NOT NULL,
    address_zip VARCHAR(20) NOT NULL,
    emergency_contact_name VARCHAR(100),
    emergency_contact_phone VARCHAR(20),
    emergency_contact_relationship VARCHAR(50),
    medical_history JSON,
    insurance_provider VARCHAR(100),
    insurance_policy_number VARCHAR(50),
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    data_encryption_key VARCHAR(255),
    audit_trail_enabled BOOLEAN DEFAULT TRUE
);
```

#### Patient Refresh Tokens Table
```sql
CREATE TABLE patient_refresh_tokens (
    id VARCHAR(36) PRIMARY KEY,
    patient_id VARCHAR(36) NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP
);
```

### MongoDB Schema

#### Patients Collection
```javascript
{
  "_id": ObjectId,
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane.smith@email.com",
  "phone_number": "+1234567890",
  "password_hash": "hashed_password",
  "date_of_birth": ISODate("1990-05-15"),
  "gender": "female",
  "address": {
    "street": "456 Main Street",
    "city": "Boston",
    "state": "MA",
    "zip": "02101"
  },
  "emergency_contact": {
    "name": "John Smith",
    "phone": "+1234567891",
    "relationship": "spouse"
  },
  "medical_history": ["Allergies to penicillin", "Previous surgery in 2018"],
  "insurance_info": {
    "provider": "Blue Cross",
    "policy_number": "BC123456789"
  },
  "email_verified": false,
  "phone_verified": false,
  "is_active": true,
  "created_at": ISODate("2024-01-15T10:30:00Z"),
  "updated_at": ISODate("2024-01-15T10:30:00Z"),
  "last_login": ISODate("2024-01-15T10:30:00Z"),
  "failed_login_attempts": 0,
  "locked_until": null,
  "login_count": 1,
  "audit_trail_enabled": true
}
```

## Security Features

### Password Security
- **Hashing**: bcrypt with 12 salt rounds
- **Complexity**: Requires uppercase, lowercase, number, and special character
- **Length**: Minimum 8 characters
- **Storage**: Never stored in plain text

### Authentication Security
- **JWT Tokens**: Short-lived access tokens (30 minutes)
- **Refresh Tokens**: Long-lived refresh tokens (30 days)
- **Account Lockout**: 5 failed attempts locks account for 30 minutes
- **Token Revocation**: Refresh tokens can be revoked on logout

### Data Security
- **Input Validation**: All inputs validated and sanitized
- **SQL Injection Protection**: Parameterized queries
- **XSS Protection**: Input sanitization
- **CSRF Protection**: Token-based authentication

### HIPAA Compliance
- **Audit Trails**: All actions logged
- **Data Encryption**: Sensitive data encrypted at rest
- **Access Control**: Role-based access control
- **Data Minimization**: Only necessary data collected

## Testing

### Running Tests
```bash
# Run all tests
pytest tests/test_patient_registration.py -v

# Run specific test class
pytest tests/test_patient_registration.py::TestPatientRegistrationValidation -v

# Run with coverage
pytest tests/test_patient_registration.py --cov=app --cov-report=html
```

### Test Categories
- **Validation Tests**: Input validation and business rules
- **Security Tests**: Password hashing, token security
- **API Tests**: Endpoint functionality and error handling
- **Database Tests**: CRUD operations and data integrity
- **HIPAA Tests**: Compliance and data security

## Usage Examples

### Python Client Example
```python
import requests

# Register a new patient
registration_data = {
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@email.com",
    "phone_number": "+1234567890",
    "password": "SecurePassword123!",
    "confirm_password": "SecurePassword123!",
    "date_of_birth": "1990-05-15",
    "gender": "female",
    "address": {
        "street": "456 Main Street",
        "city": "Boston",
        "state": "MA",
        "zip": "02101"
    }
}

response = requests.post("http://localhost:8000/api/v1/patient/register", json=registration_data)
print(response.json())

# Login
login_data = {
    "identifier": "jane.smith@email.com",
    "password": "SecurePassword123!"
}

response = requests.post("http://localhost:8000/api/v1/patient/login", json=login_data)
tokens = response.json()["data"]

# Get profile
headers = {"Authorization": f"Bearer {tokens['access_token']}"}
response = requests.get("http://localhost:8000/api/v1/patient/profile", headers=headers)
profile = response.json()
```

### cURL Examples
```bash
# Register patient
curl -X POST "http://localhost:8000/api/v1/patient/register" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@email.com",
    "phone_number": "+1234567890",
    "password": "SecurePassword123!",
    "confirm_password": "SecurePassword123!",
    "date_of_birth": "1990-05-15",
    "gender": "female",
    "address": {
      "street": "456 Main Street",
      "city": "Boston",
      "state": "MA",
      "zip": "02101"
    }
  }'

# Login
curl -X POST "http://localhost:8000/api/v1/patient/login" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "jane.smith@email.com",
    "password": "SecurePassword123!"
  }'

# Get profile (replace TOKEN with actual access token)
curl -X GET "http://localhost:8000/api/v1/patient/profile" \
  -H "Authorization: Bearer TOKEN"
```

## Error Handling

### Common Error Codes
- **400**: Bad Request - Invalid request format
- **401**: Unauthorized - Invalid or missing authentication
- **409**: Conflict - Email or phone already exists
- **422**: Validation Error - Invalid input data
- **423**: Locked - Account temporarily locked
- **500**: Internal Server Error - Server-side error

### Error Response Format
```json
{
  "success": false,
  "message": "Error description",
  "error_code": "ERROR_CODE",
  "errors": {
    "field_name": ["Specific error message"]
  }
}
```

## Configuration

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_TYPE` | Database type (postgresql/mysql/mongodb) | postgresql |
| `DATABASE_URL` | Database connection string | - |
| `MONGODB_URL` | MongoDB connection string | - |
| `SECRET_KEY` | JWT secret key | - |
| `BCRYPT_ROUNDS` | Password hashing rounds | 12 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiration | 30 |
| `SMTP_SERVER` | SMTP server for emails | - |
| `SMTP_USERNAME` | SMTP username | - |
| `SMTP_PASSWORD` | SMTP password | - |

### Rate Limiting
- **Requests per window**: 5 requests
- **Window duration**: 1 hour (3600 seconds)
- **Configurable**: Via environment variables

## Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations
- **HTTPS**: Always use HTTPS in production
- **Secret Management**: Use secure secret management
- **Database Security**: Secure database connections
- **Monitoring**: Implement logging and monitoring
- **Backup**: Regular database backups
- **Updates**: Keep dependencies updated

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
- Check the documentation

## Changelog

### Version 1.0.0
- Initial release
- Patient registration and authentication
- Database support for PostgreSQL, MySQL, and MongoDB
- Comprehensive validation and security features
- HIPAA compliance considerations
- Complete test suite 