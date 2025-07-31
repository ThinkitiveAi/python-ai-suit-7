import pytest
import jwt
import bcrypt
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from app.services.patient_service import PatientService
from app.schemas.patient_schema import PatientLoginRequest
from app.core.config import settings

client = TestClient(app)


class TestPatientLogin:
    """Test cases for patient login functionality"""

    @pytest.fixture
    def mock_patient_data(self):
        """Mock patient data for testing"""
        return {
            "id": "test-patient-id",
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@email.com",
            "phone_number": "+1234567890",
            "password_hash": bcrypt.hashpw(
                "SecurePassword123!".encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8"),
            "email_verified": True,
            "phone_verified": True,
            "is_active": True,
            "failed_login_attempts": 0,
            "locked_until": None,
        }

    @pytest.fixture
    def valid_login_request(self):
        """Valid login request data"""
        return {"email": "jane.smith@email.com", "password": "SecurePassword123!"}

    def test_login_success(self, mock_patient_data, valid_login_request):
        """Test successful patient login"""
        with (
            patch.object(
                PatientService, "_find_patient_by_email", return_value=mock_patient_data
            ),
            patch.object(PatientService, "_reset_failed_attempts"),
            patch.object(PatientService, "_update_last_login"),
            patch.object(PatientService, "_store_refresh_token"),
        ):
            service = PatientService()
            result = service.login_patient(PatientLoginRequest(**valid_login_request))

            assert result["success"] is True
            assert result["message"] == "Login successful"
            assert "access_token" in result["data"]
            assert result["data"]["expires_in"] == 1800  # 30 minutes
            assert result["data"]["token_type"] == "Bearer"
            assert "patient" in result["data"]

            # Verify patient data
            patient_data = result["data"]["patient"]
            assert patient_data["id"] == mock_patient_data["id"]
            assert patient_data["email"] == mock_patient_data["email"]
            assert patient_data["first_name"] == mock_patient_data["first_name"]
            assert patient_data["last_name"] == mock_patient_data["last_name"]

    def test_login_invalid_credentials(self, valid_login_request):
        """Test login with invalid credentials"""
        with patch.object(PatientService, "_find_patient_by_email", return_value=None):
            service = PatientService()
            result = service.login_patient(PatientLoginRequest(**valid_login_request))

            assert result["success"] is False
            assert result["message"] == "Invalid credentials"
            assert result["error_code"] == "INVALID_CREDENTIALS"

    def test_login_wrong_password(self, mock_patient_data, valid_login_request):
        """Test login with wrong password"""
        with (
            patch.object(
                PatientService, "_find_patient_by_email", return_value=mock_patient_data
            ),
            patch.object(PatientService, "_increment_failed_attempts"),
        ):
            # Use wrong password
            valid_login_request["password"] = "WrongPassword123!"
            service = PatientService()
            result = service.login_patient(PatientLoginRequest(**valid_login_request))

            assert result["success"] is False
            assert result["message"] == "Invalid credentials"
            assert result["error_code"] == "INVALID_CREDENTIALS"

    def test_login_account_locked(self, mock_patient_data, valid_login_request):
        """Test login with locked account"""
        # Set account as locked
        mock_patient_data["locked_until"] = (
            datetime.utcnow() + timedelta(minutes=30)
        ).isoformat()

        with patch.object(
            PatientService, "_find_patient_by_email", return_value=mock_patient_data
        ):
            service = PatientService()
            result = service.login_patient(PatientLoginRequest(**valid_login_request))

            assert result["success"] is False
            assert "locked" in result["message"].lower()
            assert result["error_code"] == "ACCOUNT_LOCKED"

    def test_login_account_deactivated(self, mock_patient_data, valid_login_request):
        """Test login with deactivated account"""
        # Set account as inactive
        mock_patient_data["is_active"] = False

        with patch.object(
            PatientService, "_find_patient_by_email", return_value=mock_patient_data
        ):
            service = PatientService()
            result = service.login_patient(PatientLoginRequest(**valid_login_request))

            assert result["success"] is False
            assert result["message"] == "Account is deactivated"
            assert result["error_code"] == "ACCOUNT_DEACTIVATED"

    def test_jwt_token_structure(self, mock_patient_data, valid_login_request):
        """Test JWT token structure and payload"""
        with (
            patch.object(
                PatientService, "_find_patient_by_email", return_value=mock_patient_data
            ),
            patch.object(PatientService, "_reset_failed_attempts"),
            patch.object(PatientService, "_update_last_login"),
            patch.object(PatientService, "_store_refresh_token"),
        ):
            service = PatientService()
            result = service.login_patient(PatientLoginRequest(**valid_login_request))

            # Decode and verify JWT token
            token = result["data"]["access_token"]
            payload = jwt.decode(
                token, settings.secret_key, algorithms=[settings.algorithm]
            )

            # Verify payload structure
            assert "patient_id" in payload
            assert "email" in payload
            assert "role" in payload
            assert "exp" in payload
            assert "iat" in payload

            # Verify payload values
            assert payload["patient_id"] == mock_patient_data["id"]
            assert payload["email"] == mock_patient_data["email"]
            assert payload["role"] == "patient"

            # Verify token expiry (should be 30 minutes from issued at time)
            exp_timestamp = payload["exp"]
            iat_timestamp = payload["iat"]
            time_diff_seconds = exp_timestamp - iat_timestamp

            # Should be exactly 30 minutes (1800 seconds)
            assert time_diff_seconds == 1800

    def test_bcrypt_password_validation(self):
        """Test bcrypt password hashing and verification"""
        password = "SecurePassword123!"

        # Hash password
        service = PatientService()
        hashed_password = service._hash_password(password)

        # Verify password
        assert service._verify_password(password, hashed_password) is True

        # Verify wrong password fails
        assert service._verify_password("WrongPassword123!", hashed_password) is False

    def test_api_endpoint_success(self, mock_patient_data, valid_login_request):
        """Test the actual API endpoint for successful login"""
        with (
            patch.object(
                PatientService, "_find_patient_by_email", return_value=mock_patient_data
            ),
            patch.object(PatientService, "_reset_failed_attempts"),
            patch.object(PatientService, "_update_last_login"),
            patch.object(PatientService, "_store_refresh_token"),
        ):
            response = client.post("/api/v1/patient/login", json=valid_login_request)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Login successful"
            assert "access_token" in data["data"]
            assert data["data"]["expires_in"] == 1800
            assert data["data"]["token_type"] == "Bearer"

    def test_api_endpoint_invalid_email_format(self):
        """Test API endpoint with invalid email format"""
        invalid_request = {"email": "invalid-email", "password": "SecurePassword123!"}

        response = client.post("/api/v1/patient/login", json=invalid_request)

        assert response.status_code == 422  # Validation error

    def test_api_endpoint_empty_password(self):
        """Test API endpoint with empty password"""
        invalid_request = {"email": "jane.smith@email.com", "password": ""}

        response = client.post("/api/v1/patient/login", json=invalid_request)

        assert response.status_code == 422  # Validation error

    def test_api_endpoint_missing_fields(self):
        """Test API endpoint with missing required fields"""
        # Missing email
        response = client.post(
            "/api/v1/patient/login", json={"password": "SecurePassword123!"}
        )
        assert response.status_code == 422

        # Missing password
        response = client.post(
            "/api/v1/patient/login", json={"email": "jane.smith@email.com"}
        )
        assert response.status_code == 422

    def test_account_lockout_after_failed_attempts(
        self, mock_patient_data, valid_login_request
    ):
        """Test account lockout after multiple failed attempts"""
        # Set failed attempts to 4 (one more will trigger lockout)
        mock_patient_data["failed_login_attempts"] = 4

        with (
            patch.object(
                PatientService, "_find_patient_by_email", return_value=mock_patient_data
            ),
            patch.object(PatientService, "_increment_failed_attempts"),
            patch.object(PatientService, "_lock_account"),
        ):
            # Use wrong password
            valid_login_request["password"] = "WrongPassword123!"
            service = PatientService()
            result = service.login_patient(PatientLoginRequest(**valid_login_request))

            assert result["success"] is False
            assert "locked" in result["message"].lower()
            assert result["error_code"] == "ACCOUNT_LOCKED"

    def test_reset_failed_attempts_on_success(
        self, mock_patient_data, valid_login_request
    ):
        """Test that failed attempts are reset on successful login"""
        # Set some failed attempts
        mock_patient_data["failed_login_attempts"] = 3

        with (
            patch.object(
                PatientService, "_find_patient_by_email", return_value=mock_patient_data
            ),
            patch.object(PatientService, "_reset_failed_attempts") as mock_reset,
            patch.object(PatientService, "_update_last_login"),
            patch.object(PatientService, "_store_refresh_token"),
        ):
            service = PatientService()
            result = service.login_patient(PatientLoginRequest(**valid_login_request))

            assert result["success"] is True
            mock_reset.assert_called_once_with(mock_patient_data["id"])

    def test_token_expiry_handling(self):
        """Test that expired tokens are properly handled"""
        # Create an expired token
        expired_payload = {
            "patient_id": "test-id",
            "email": "test@example.com",
            "role": "patient",
            "exp": datetime.utcnow() - timedelta(minutes=1),  # Expired 1 minute ago
            "iat": datetime.utcnow() - timedelta(minutes=31),
        }

        expired_token = jwt.encode(
            expired_payload, settings.secret_key, algorithm=settings.algorithm
        )

        # Try to verify the expired token
        from app.utils.auth_utils import verify_patient_token

        with pytest.raises(Exception) as exc_info:
            verify_patient_token(expired_token)

        # Should raise an HTTPException with 401 status
        assert hasattr(exc_info.value, "status_code")
        assert exc_info.value.status_code == 401

    def test_invalid_token_handling(self):
        """Test handling of invalid tokens"""
        from app.utils.auth_utils import verify_patient_token

        # Test with invalid token
        with pytest.raises(Exception) as exc_info:
            verify_patient_token("invalid.token.here")

        # Should raise an HTTPException with 401 status
        assert hasattr(exc_info.value, "status_code")
        assert exc_info.value.status_code == 401

    def test_token_role_validation(self):
        """Test that tokens with wrong role are rejected"""
        # Create token with wrong role
        wrong_role_payload = {
            "patient_id": "test-id",
            "email": "test@example.com",
            "role": "admin",  # Wrong role
            "exp": datetime.utcnow() + timedelta(minutes=30),
            "iat": datetime.utcnow(),
        }

        wrong_role_token = jwt.encode(
            wrong_role_payload, settings.secret_key, algorithm=settings.algorithm
        )

        from app.utils.auth_utils import verify_patient_token

        with pytest.raises(Exception) as exc_info:
            verify_patient_token(wrong_role_token)

        # Should raise an HTTPException with 401 status
        assert hasattr(exc_info.value, "status_code")
        assert exc_info.value.status_code == 401
