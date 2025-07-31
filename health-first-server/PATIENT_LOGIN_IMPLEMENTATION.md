# Patient Login Implementation

## Overview

This document describes the implementation of a secure JWT-based login flow for patients in the Health First application. The implementation follows the user story requirements and provides comprehensive security features.

## User Story

**As a patient, I want to securely log in using my email and password so I can access my health information and services.**

## API Endpoint

### POST /api/v1/patient/login

**Request Body:**
```json
{
  "email": "jane.smith@email.com",
  "password": "SecurePassword123!"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "jwt-access-token-here",
    "expires_in": 1800,
    "token_type": "Bearer",
    "patient": {
      "id": "patient-id",
      "first_name": "Jane",
      "last_name": "Smith",
      "email": "jane.smith@email.com",
      "phone_number": "+1234567890",
      "email_verified": true,
      "phone_verified": true,
      "is_active": true
    }
  }
}
```

## JWT Token Configuration

- **Token Type**: Bearer
- **Expiry**: 30 minutes (1800 seconds)
- **Payload Fields**: 
  - `patient_id`: Patient's unique identifier
  - `email`: Patient's email address
  - `role`: "patient"
  - `exp`: Expiration timestamp
  - `iat`: Issued at timestamp

## Authentication Logic

1. **Input Validation**: Validates email format and password presence
2. **Patient Lookup**: Finds patient by email address
3. **Account Status Check**: Verifies account is active and not locked
4. **Password Verification**: Uses bcrypt to verify password against stored hash
5. **Security Measures**: 
   - Tracks failed login attempts
   - Locks account after 5 failed attempts for 30 minutes
   - Resets failed attempts on successful login
6. **Token Generation**: Creates JWT access token with 30-minute expiry
7. **Response**: Returns token and patient information

## Validation Rules

### Email Validation
- Must be valid email format (using Pydantic EmailStr)
- Case-insensitive lookup

### Password Validation
- Must be provided and non-empty
- Validated against bcrypt hash

## Security Features

### Account Lockout
- Tracks failed login attempts
- Locks account after 5 failed attempts
- 30-minute lockout duration
- Automatic unlock after lockout period

### Password Security
- bcrypt hashing with configurable rounds (12 by default)
- Secure password verification
- No plain text password storage

### JWT Security
- 30-minute token expiry
- Role-based access control
- Secure token generation with proper payload structure

## Error Handling

### 401 Unauthorized
- Invalid credentials
- Account deactivated
- Invalid token

### 423 Locked
- Account locked due to failed attempts

### 422 Validation Error
- Invalid email format
- Missing required fields
- Empty password

### 500 Internal Server Error
- Database errors
- Token generation failures

## Database Integration

### Supported Databases
- PostgreSQL
- MySQL
- MongoDB

### Patient Model Fields
- `id`: Unique identifier
- `email`: Email address (unique, indexed)
- `password_hash`: bcrypt hashed password
- `is_active`: Account status
- `failed_login_attempts`: Failed login counter
- `locked_until`: Account lockout timestamp
- `email_verified`: Email verification status
- `phone_verified`: Phone verification status

## Testing

### Unit Tests Coverage

The implementation includes comprehensive unit tests covering:

1. **Login Success**: Valid credentials and proper response format
2. **Invalid Credentials**: Wrong email or password
3. **Account Lockout**: Multiple failed attempts and account locking
4. **Account Status**: Deactivated account handling
5. **JWT Token Structure**: Token payload validation and expiry
6. **bcrypt Validation**: Password hashing and verification
7. **API Endpoint Testing**: Full HTTP request/response testing
8. **Input Validation**: Email format and required field validation
9. **Token Expiry Handling**: Expired token rejection
10. **Invalid Token Handling**: Malformed token rejection
11. **Role Validation**: Wrong role token rejection

### Test Files
- `tests/test_patient_login.py`: Comprehensive test suite with 16 test cases

## Implementation Files

### Core Implementation
- `app/controllers/patient_controller.py`: API endpoint handler
- `app/services/patient_service.py`: Business logic and authentication
- `app/schemas/patient_schema.py`: Request/response models
- `app/utils/auth_utils.py`: JWT token utilities

### Key Methods

#### PatientService.login_patient()
- Main authentication method
- Handles all login logic and security measures
- Returns standardized response format

#### PatientService._generate_tokens()
- Creates JWT access and refresh tokens
- Implements 30-minute expiry for access tokens
- Includes proper payload structure

#### PatientService._verify_password()
- bcrypt password verification
- Secure comparison against stored hash

#### verify_patient_token()
- JWT token validation
- Role and expiry checking
- Proper error handling

## Configuration

### Environment Variables
- `SECRET_KEY`: JWT signing secret
- `ALGORITHM`: JWT algorithm (HS256)
- `BCRYPT_ROUNDS`: Password hashing rounds (12)

### Token Settings
- Access token expiry: 30 minutes
- Refresh token expiry: 30 days
- Token type: Bearer

## Middleware Integration

The login endpoint integrates with existing middleware:
- Rate limiting
- Request validation
- CORS handling
- Error handling

## Security Best Practices

1. **Password Security**: bcrypt hashing with salt
2. **Token Security**: Short-lived access tokens
3. **Account Protection**: Brute force protection with lockout
4. **Input Validation**: Comprehensive request validation
5. **Error Handling**: Secure error messages without information leakage
6. **Database Security**: Parameterized queries and proper indexing

## Usage Example

```python
import requests

# Login request
response = requests.post(
    "http://localhost:8000/api/v1/patient/login",
    json={
        "email": "jane.smith@email.com",
        "password": "SecurePassword123!"
    }
)

if response.status_code == 200:
    data = response.json()
    access_token = data["data"]["access_token"]
    
    # Use token for authenticated requests
    headers = {"Authorization": f"Bearer {access_token}"}
    profile_response = requests.get(
        "http://localhost:8000/api/v1/patient/profile",
        headers=headers
    )
```

## Future Enhancements

1. **Refresh Token Endpoint**: Implement token refresh functionality
2. **Multi-Factor Authentication**: Add SMS/email verification
3. **Session Management**: Track active sessions
4. **Audit Logging**: Log login attempts and security events
5. **Password Reset**: Implement secure password reset flow

## Conclusion

The patient login implementation provides a secure, robust authentication system that meets all the requirements specified in the user story. The implementation includes comprehensive security measures, proper error handling, and extensive test coverage to ensure reliability and security. 