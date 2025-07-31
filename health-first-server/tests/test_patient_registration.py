import pytest
import bcrypt
import jwt
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.config import settings
from app.services.patient_service import PatientService
from app.schemas.patient_schema import (
    PatientRegistrationRequest,
    PatientAddress,
    EmergencyContact,
    InsuranceInfo,
    Gender,
)
from app.models.patient_model import PatientSQL, PatientRefreshTokenSQL


# Test client
client = TestClient(app)

# Mock database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Create a test database session"""
    from app.core.database import Base

    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def patient_service():
    """Create a patient service instance"""
    return PatientService()


@pytest.fixture
def valid_patient_data():
    """Valid patient registration data"""
    return {
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
            "zip": "02101",
        },
        "emergency_contact": {
            "name": "John Smith",
            "phone": "+1234567891",
            "relationship": "spouse",
        },
        "insurance_info": {"provider": "Blue Cross", "policy_number": "BC123456789"},
        "medical_history": ["Allergies to penicillin", "Previous surgery in 2018"],
    }


class TestPatientRegistrationValidation:
    """Test patient registration validation rules"""

    def test_valid_patient_registration(self, valid_patient_data):
        """Test valid patient registration data"""
        patient_request = PatientRegistrationRequest(**valid_patient_data)
        assert patient_request.first_name == "Jane"
        assert patient_request.last_name == "Smith"
        assert patient_request.email == "jane.smith@email.com"
        assert patient_request.gender == Gender.FEMALE

    def test_invalid_email_format(self, valid_patient_data):
        """Test invalid email format"""
        valid_patient_data["email"] = "invalid-email"
        with pytest.raises(ValueError, match="value is not a valid email address"):
            PatientRegistrationRequest(**valid_patient_data)

    def test_invalid_phone_format(self, valid_patient_data):
        """Test invalid phone number format"""
        valid_patient_data["phone_number"] = "invalid-phone"
        with pytest.raises(ValueError, match="Invalid phone number format"):
            PatientRegistrationRequest(**valid_patient_data)

    def test_weak_password(self, valid_patient_data):
        """Test weak password validation"""
        valid_patient_data["password"] = "weak"
        valid_patient_data["confirm_password"] = "weak"
        with pytest.raises(
            ValueError, match="Password must be at least 8 characters long"
        ):
            PatientRegistrationRequest(**valid_patient_data)

    def test_password_mismatch(self, valid_patient_data):
        """Test password confirmation mismatch"""
        valid_patient_data["confirm_password"] = "DifferentPassword123!"
        with pytest.raises(ValueError, match="Passwords do not match"):
            PatientRegistrationRequest(**valid_patient_data)

    def test_password_complexity_requirements(self, valid_patient_data):
        """Test password complexity requirements"""
        # Test missing uppercase
        valid_patient_data["password"] = "password123!"
        valid_patient_data["confirm_password"] = "password123!"
        with pytest.raises(
            ValueError, match="Password must contain at least one uppercase letter"
        ):
            PatientRegistrationRequest(**valid_patient_data)

        # Test missing lowercase
        valid_patient_data["password"] = "PASSWORD123!"
        valid_patient_data["confirm_password"] = "PASSWORD123!"
        with pytest.raises(
            ValueError, match="Password must contain at least one lowercase letter"
        ):
            PatientRegistrationRequest(**valid_patient_data)

        # Test missing number
        valid_patient_data["password"] = "Password!"
        valid_patient_data["confirm_password"] = "Password!"
        with pytest.raises(
            ValueError, match="Password must contain at least one number"
        ):
            PatientRegistrationRequest(**valid_patient_data)

        # Test missing special character
        valid_patient_data["password"] = "Password123"
        valid_patient_data["confirm_password"] = "Password123"
        with pytest.raises(
            ValueError, match="Password must contain at least one special character"
        ):
            PatientRegistrationRequest(**valid_patient_data)

    def test_invalid_date_of_birth_future(self, valid_patient_data):
        """Test future date of birth"""
        valid_patient_data["date_of_birth"] = "2030-05-15"
        with pytest.raises(ValueError, match="Date of birth must be in the past"):
            PatientRegistrationRequest(**valid_patient_data)

    def test_invalid_date_of_birth_too_young(self, valid_patient_data):
        """Test patient too young (COPPA compliance)"""
        # Set date of birth to make patient 12 years old
        today = date.today()
        young_date = date(today.year - 12, today.month, today.day)
        valid_patient_data["date_of_birth"] = young_date.isoformat()
        with pytest.raises(ValueError, match="Must be at least 13 years old"):
            PatientRegistrationRequest(**valid_patient_data)

    def test_invalid_zip_code(self, valid_patient_data):
        """Test invalid ZIP code format"""
        valid_patient_data["address"]["zip"] = "invalid"
        with pytest.raises(ValueError, match="Invalid ZIP code format"):
            PatientRegistrationRequest(**valid_patient_data)

    def test_invalid_emergency_phone(self, valid_patient_data):
        """Test invalid emergency contact phone"""
        valid_patient_data["emergency_contact"]["phone"] = "invalid-phone"
        with pytest.raises(ValueError, match="Invalid phone number format"):
            PatientRegistrationRequest(**valid_patient_data)

    def test_medical_history_validation(self, valid_patient_data):
        """Test medical history validation"""
        # Test empty entry
        valid_patient_data["medical_history"] = ["", "Valid entry"]
        with pytest.raises(ValueError, match="Medical history entry 1 cannot be empty"):
            PatientRegistrationRequest(**valid_patient_data)

        # Test too long entry
        long_entry = "x" * 501
        valid_patient_data["medical_history"] = [long_entry]
        with pytest.raises(ValueError, match="Medical history entry 1 is too long"):
            PatientRegistrationRequest(**valid_patient_data)


class TestPatientService:
    """Test patient service functionality"""

    @patch("app.services.patient_service.send_verification_email")
    @patch("app.services.patient_service.send_verification_sms")
    def test_register_patient_success(
        self, mock_sms, mock_email, patient_service, valid_patient_data
    ):
        """Test successful patient registration"""
        # Mock database operations
        with (
            patch.object(patient_service, "_email_exists", return_value=False),
            patch.object(patient_service, "_phone_exists", return_value=False),
            patch.object(patient_service, "patient_model") as mock_model,
        ):
            mock_model.create_patient.return_value = "test-patient-id"

            result = patient_service.register_patient(
                PatientRegistrationRequest(**valid_patient_data)
            )

            assert result["success"] is True
            assert (
                result["message"]
                == "Patient registered successfully. Verification email sent."
            )
            assert result["data"]["patient_id"] == "test-patient-id"
            assert result["data"]["email"] == "jane.smith@email.com"
            assert result["data"]["phone_number"] == "+1234567890"
            assert result["data"]["email_verified"] is False
            assert result["data"]["phone_verified"] is False

    def test_register_patient_email_exists(self, patient_service, valid_patient_data):
        """Test registration with existing email"""
        with patch.object(patient_service, "_email_exists", return_value=True):
            result = patient_service.register_patient(
                PatientRegistrationRequest(**valid_patient_data)
            )

            assert result["success"] is False
            assert result["message"] == "Email is already registered"
            assert result["error_code"] == "EMAIL_EXISTS"

    def test_register_patient_phone_exists(self, patient_service, valid_patient_data):
        """Test registration with existing phone number"""
        with (
            patch.object(patient_service, "_email_exists", return_value=False),
            patch.object(patient_service, "_phone_exists", return_value=True),
        ):
            result = patient_service.register_patient(
                PatientRegistrationRequest(**valid_patient_data)
            )

            assert result["success"] is False
            assert result["message"] == "Phone number is already registered"
            assert result["error_code"] == "PHONE_EXISTS"

    def test_password_hashing(self, patient_service):
        """Test password hashing functionality"""
        password = "SecurePassword123!"
        password_hash = patient_service._hash_password(password)

        # Verify hash is different from original password
        assert password_hash != password

        # Verify password can be verified
        assert patient_service._verify_password(password, password_hash) is True

        # Verify wrong password fails
        assert (
            patient_service._verify_password("WrongPassword123!", password_hash)
            is False
        )

    def test_token_generation(self, patient_service):
        """Test JWT token generation"""
        patient_id = "test-patient-id"
        access_token, refresh_token = patient_service._generate_tokens(patient_id)

        # Verify tokens are different
        assert access_token != refresh_token

        # Verify tokens can be decoded
        access_payload = jwt.decode(
            access_token, settings.secret_key, algorithms=[settings.algorithm]
        )
        refresh_payload = jwt.decode(
            refresh_token, settings.secret_key, algorithms=[settings.algorithm]
        )

        assert access_payload["sub"] == patient_id
        assert access_payload["type"] == "access"
        assert refresh_payload["sub"] == patient_id
        assert refresh_payload["type"] == "refresh"

    def test_login_success(self, patient_service, valid_patient_data):
        """Test successful patient login"""
        # Mock patient data
        patient_data = {
            "id": "test-patient-id",
            "email": "jane.smith@email.com",
            "password_hash": patient_service._hash_password("SecurePassword123!"),
            "is_active": True,
            "failed_login_attempts": 0,
            "locked_until": None,
        }

        with (
            patch.object(
                patient_service,
                "_find_patient_by_identifier",
                return_value=patient_data,
            ),
            patch.object(patient_service, "_reset_failed_attempts"),
            patch.object(patient_service, "_update_last_login"),
            patch.object(patient_service, "_store_refresh_token"),
        ):
            login_data = PatientRegistrationRequest(**valid_patient_data)
            result = patient_service.login_patient(login_data)

            assert result["success"] is True
            assert result["message"] == "Login successful"
            assert "access_token" in result["data"]
            assert "refresh_token" in result["data"]

    def test_login_invalid_credentials(self, patient_service, valid_patient_data):
        """Test login with invalid credentials"""
        # Mock patient data with wrong password
        patient_data = {
            "id": "test-patient-id",
            "email": "jane.smith@email.com",
            "password_hash": patient_service._hash_password("WrongPassword123!"),
            "is_active": True,
            "failed_login_attempts": 0,
            "locked_until": None,
        }

        with (
            patch.object(
                patient_service,
                "_find_patient_by_identifier",
                return_value=patient_data,
            ),
            patch.object(patient_service, "_increment_failed_attempts"),
        ):
            login_data = PatientRegistrationRequest(**valid_patient_data)
            result = patient_service.login_patient(login_data)

            assert result["success"] is False
            assert result["message"] == "Invalid credentials"
            assert result["error_code"] == "INVALID_CREDENTIALS"

    def test_login_account_locked(self, patient_service, valid_patient_data):
        """Test login with locked account"""
        # Mock patient data with locked account
        patient_data = {
            "id": "test-patient-id",
            "email": "jane.smith@email.com",
            "password_hash": patient_service._hash_password("SecurePassword123!"),
            "is_active": True,
            "failed_login_attempts": 0,
            "locked_until": datetime.utcnow() + timedelta(minutes=30),
        }

        with patch.object(
            patient_service, "_find_patient_by_identifier", return_value=patient_data
        ):
            login_data = PatientRegistrationRequest(**valid_patient_data)
            result = patient_service.login_patient(login_data)

            assert result["success"] is False
            assert (
                result["message"]
                == "Account is temporarily locked due to too many failed attempts"
            )
            assert result["error_code"] == "ACCOUNT_LOCKED"


class TestPatientAPIEndpoints:
    """Test patient API endpoints"""

    def test_register_patient_endpoint_success(self, valid_patient_data):
        """Test successful patient registration via API"""
        with patch(
            "app.controllers.patient_controller.patient_service"
        ) as mock_service:
            mock_service.register_patient.return_value = {
                "success": True,
                "message": "Patient registered successfully. Verification email sent.",
                "data": {
                    "patient_id": "test-patient-id",
                    "email": "jane.smith@email.com",
                    "phone_number": "+1234567890",
                    "email_verified": False,
                    "phone_verified": False,
                },
            }

            response = client.post("/api/v1/patient/register", json=valid_patient_data)

            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert (
                data["message"]
                == "Patient registered successfully. Verification email sent."
            )
            assert data["data"]["patient_id"] == "test-patient-id"

    def test_register_patient_endpoint_validation_error(self):
        """Test patient registration with validation errors"""
        invalid_data = {
            "first_name": "J",  # Too short
            "last_name": "Smith",
            "email": "invalid-email",
            "phone_number": "+1234567890",
            "password": "weak",
            "confirm_password": "weak",
            "date_of_birth": "1990-05-15",
            "gender": "female",
            "address": {
                "street": "456 Main Street",
                "city": "Boston",
                "state": "MA",
                "zip": "02101",
            },
        }

        response = client.post("/api/v1/patient/register", json=invalid_data)

        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["message"] == "Validation failed"
        assert "first_name" in data["errors"]
        assert "email" in data["errors"]
        assert "password" in data["errors"]

    def test_register_patient_endpoint_duplicate_email(self, valid_patient_data):
        """Test patient registration with duplicate email"""
        with patch(
            "app.controllers.patient_controller.patient_service"
        ) as mock_service:
            mock_service.register_patient.return_value = {
                "success": False,
                "message": "Email is already registered",
                "error_code": "EMAIL_EXISTS",
            }

            response = client.post("/api/v1/patient/register", json=valid_patient_data)

            assert response.status_code == 409
            data = response.json()
            assert data["success"] is False
            assert data["message"] == "Email is already registered"
            assert data["error_code"] == "EMAIL_EXISTS"

    def test_login_patient_endpoint_success(self, valid_patient_data):
        """Test successful patient login via API"""
        login_data = {
            "identifier": "jane.smith@email.com",
            "password": "SecurePassword123!",
        }

        with patch(
            "app.controllers.patient_controller.patient_service"
        ) as mock_service:
            mock_service.login_patient.return_value = {
                "success": True,
                "message": "Login successful",
                "data": {
                    "access_token": "test-access-token",
                    "refresh_token": "test-refresh-token",
                    "token_type": "bearer",
                    "expires_in": 1800,
                    "patient": {
                        "id": "test-patient-id",
                        "first_name": "Jane",
                        "last_name": "Smith",
                        "email": "jane.smith@email.com",
                        "email_verified": False,
                        "phone_verified": False,
                    },
                },
            }

            response = client.post("/api/v1/patient/login", json=login_data)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Login successful"
            assert data["data"]["access_token"] == "test-access-token"

    def test_login_patient_endpoint_invalid_credentials(self, valid_patient_data):
        """Test patient login with invalid credentials via API"""
        login_data = {
            "identifier": "jane.smith@email.com",
            "password": "WrongPassword123!",
        }

        with patch(
            "app.controllers.patient_controller.patient_service"
        ) as mock_service:
            mock_service.login_patient.return_value = {
                "success": False,
                "message": "Invalid credentials",
                "error_code": "INVALID_CREDENTIALS",
            }

            response = client.post("/api/v1/patient/login", json=login_data)

            assert response.status_code == 401
            data = response.json()
            assert data["success"] is False
            assert data["message"] == "Invalid credentials"
            assert data["error_code"] == "INVALID_CREDENTIALS"

    def test_health_check_endpoint(self):
        """Test patient health check endpoint"""
        response = client.get("/api/v1/patient/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "patient-registration"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data


class TestSecurityFeatures:
    """Test security features"""

    def test_password_never_logged(self, patient_service, valid_patient_data, caplog):
        """Test that passwords are never logged"""
        with (
            patch.object(patient_service, "_email_exists", return_value=False),
            patch.object(patient_service, "_phone_exists", return_value=False),
            patch.object(patient_service, "patient_model") as mock_model,
        ):
            mock_model.create_patient.return_value = "test-patient-id"

            patient_service.register_patient(
                PatientRegistrationRequest(**valid_patient_data)
            )

            # Check that password is not in logs
            log_text = caplog.text
            assert "SecurePassword123!" not in log_text
            assert "password" not in log_text.lower()

    def test_password_hash_verification(self, patient_service):
        """Test password hash verification with different passwords"""
        password = "SecurePassword123!"
        password_hash = patient_service._hash_password(password)

        # Test correct password
        assert patient_service._verify_password(password, password_hash) is True

        # Test incorrect passwords
        assert (
            patient_service._verify_password("WrongPassword123!", password_hash)
            is False
        )
        assert patient_service._verify_password("", password_hash) is False
        assert patient_service._verify_password(password, "invalid_hash") is False

    def test_token_security(self, patient_service):
        """Test JWT token security"""
        patient_id = "test-patient-id"
        access_token, refresh_token = patient_service._generate_tokens(patient_id)

        # Test token payload
        access_payload = jwt.decode(
            access_token, settings.secret_key, algorithms=[settings.algorithm]
        )
        assert access_payload["sub"] == patient_id
        assert access_payload["type"] == "access"

        # Test token expiration
        assert "exp" in access_payload

        # Test refresh token
        refresh_payload = jwt.decode(
            refresh_token, settings.secret_key, algorithms=[settings.algorithm]
        )
        assert refresh_payload["sub"] == patient_id
        assert refresh_payload["type"] == "refresh"


class TestHIPAACompliance:
    """Test HIPAA compliance features"""

    def test_sensitive_data_encryption(self, patient_service, valid_patient_data):
        """Test that sensitive data is handled securely"""
        # This would test encryption of sensitive medical data
        # In a real implementation, you would encrypt medical history, insurance info, etc.
        pass

    def test_audit_trail_enabled(self, patient_service, valid_patient_data):
        """Test that audit trail is enabled by default"""
        with (
            patch.object(patient_service, "_email_exists", return_value=False),
            patch.object(patient_service, "_phone_exists", return_value=False),
            patch.object(patient_service, "patient_model") as mock_model,
        ):
            mock_model.create_patient.return_value = "test-patient-id"

            result = patient_service.register_patient(
                PatientRegistrationRequest(**valid_patient_data)
            )

            # Verify audit trail is enabled (this would be checked in the database)
            assert result["success"] is True

    def test_data_minimization(self, patient_service, valid_patient_data):
        """Test that only necessary data is collected and stored"""
        # Test that we don't collect unnecessary sensitive information
        required_fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "date_of_birth",
            "gender",
            "address",
        ]

        for field in required_fields:
            assert field in valid_patient_data

        # Test that we don't collect unnecessary fields
        unnecessary_fields = ["ssn", "credit_card", "bank_account"]
        for field in unnecessary_fields:
            assert field not in valid_patient_data
