import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from app.main import app
from app.services.provider_service import ProviderService
from app.services.validation_service import ValidationService
from app.utils.password_utils import hash_password, verify_password
from app.core.database import VerificationStatus


client = TestClient(app)


class TestProviderRegistration:
    """Test cases for provider registration functionality."""

    @pytest.fixture
    def valid_provider_data(self):
        """Valid provider registration data."""
        return {
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
                "zip": "10001",
            },
        }

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def mock_mongo_collection(self):
        """Mock MongoDB collection."""
        return Mock()

    def test_valid_provider_registration(self, valid_provider_data):
        """Test successful provider registration."""
        with patch(
            "app.controllers.provider_controller.ProviderService"
        ) as mock_service:
            # Mock successful registration
            mock_service_instance = Mock()
            mock_service_instance.register_provider.return_value = (
                True,
                {
                    "success": True,
                    "message": "Provider registered successfully. Verification email sent.",
                    "data": {
                        "provider_id": "test-uuid-123",
                        "email": "john.doe@clinic.com",
                        "verification_status": "pending",
                    },
                },
                None,
            )
            mock_service.return_value = mock_service_instance

            response = client.post(
                "/api/v1/provider/register", json=valid_provider_data
            )

            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert "provider_id" in data["data"]
            assert data["data"]["email"] == "john.doe@clinic.com"
            assert data["data"]["verification_status"] == "pending"

    def test_invalid_email_format(self, valid_provider_data):
        """Test registration with invalid email format."""
        invalid_data = valid_provider_data.copy()
        invalid_data["email"] = "invalid-email"

        response = client.post("/api/v1/provider/register", json=invalid_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_weak_password(self, valid_provider_data):
        """Test registration with weak password."""
        invalid_data = valid_provider_data.copy()
        invalid_data["password"] = "weak"
        invalid_data["confirm_password"] = "weak"

        response = client.post("/api/v1/provider/register", json=invalid_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_password_mismatch(self, valid_provider_data):
        """Test registration with password mismatch."""
        invalid_data = valid_provider_data.copy()
        invalid_data["confirm_password"] = "DifferentPassword123!"

        response = client.post("/api/v1/provider/register", json=invalid_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_invalid_phone_number(self, valid_provider_data):
        """Test registration with invalid phone number."""
        invalid_data = valid_provider_data.copy()
        invalid_data["phone_number"] = "invalid-phone"

        response = client.post("/api/v1/provider/register", json=invalid_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_invalid_specialization(self, valid_provider_data):
        """Test registration with invalid specialization."""
        invalid_data = valid_provider_data.copy()
        invalid_data["specialization"] = "InvalidSpecialization"

        response = client.post("/api/v1/provider/register", json=invalid_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_missing_required_fields(self):
        """Test registration with missing required fields."""
        incomplete_data = {
            "first_name": "John",
            "email": "john.doe@clinic.com",
            # Missing other required fields
        }

        response = client.post("/api/v1/provider/register", json=incomplete_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_duplicate_email_registration(self, valid_provider_data):
        """Test registration with duplicate email."""
        with patch(
            "app.controllers.provider_controller.ProviderService"
        ) as mock_service:
            # Mock duplicate email error
            mock_service_instance = Mock()
            mock_service_instance.register_provider.return_value = (
                False,
                {"success": False, "message": "Email address is already registered"},
                "Email address is already registered",
            )
            mock_service.return_value = mock_service_instance

            response = client.post(
                "/api/v1/provider/register", json=valid_provider_data
            )

            assert response.status_code == 409
            data = response.json()
            assert data["success"] is False
            assert "already registered" in data["message"].lower()

    def test_duplicate_phone_registration(self, valid_provider_data):
        """Test registration with duplicate phone number."""
        with patch(
            "app.controllers.provider_controller.ProviderService"
        ) as mock_service:
            # Mock duplicate phone error
            mock_service_instance = Mock()
            mock_service_instance.register_provider.return_value = (
                False,
                {"success": False, "message": "Phone number is already registered"},
                "Phone number is already registered",
            )
            mock_service.return_value = mock_service_instance

            response = client.post(
                "/api/v1/provider/register", json=valid_provider_data
            )

            assert response.status_code == 409
            data = response.json()
            assert data["success"] is False
            assert "already registered" in data["message"].lower()

    def test_duplicate_license_registration(self, valid_provider_data):
        """Test registration with duplicate license number."""
        with patch(
            "app.controllers.provider_controller.ProviderService"
        ) as mock_service:
            # Mock duplicate license error
            mock_service_instance = Mock()
            mock_service_instance.register_provider.return_value = (
                False,
                {"success": False, "message": "License number is already registered"},
                "License number is already registered",
            )
            mock_service.return_value = mock_service_instance

            response = client.post(
                "/api/v1/provider/register", json=valid_provider_data
            )

            assert response.status_code == 409
            data = response.json()
            assert data["success"] is False
            assert "already registered" in data["message"].lower()

    def test_validation_errors(self, valid_provider_data):
        """Test registration with validation errors."""
        with patch(
            "app.controllers.provider_controller.ProviderService"
        ) as mock_service:
            # Mock validation errors
            mock_service_instance = Mock()
            mock_service_instance.register_provider.return_value = (
                False,
                {
                    "success": False,
                    "message": "Validation failed",
                    "errors": {
                        "email": ["Invalid email format"],
                        "phone_number": ["Invalid phone number format"],
                    },
                },
                "Validation errors found",
            )
            mock_service.return_value = mock_service_instance

            response = client.post(
                "/api/v1/provider/register", json=valid_provider_data
            )

            assert response.status_code == 422
            data = response.json()
            assert data["success"] is False
            assert "errors" in data
            assert "email" in data["errors"]
            assert "phone_number" in data["errors"]


class TestPasswordUtils:
    """Test cases for password utility functions."""

    def test_password_hashing(self):
        """Test password hashing functionality."""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > len(password)
        assert verify_password(password, hashed) is True

    def test_password_verification(self):
        """Test password verification functionality."""
        password = "SecurePassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password(wrong_password, hashed) is False

    def test_password_strength_validation(self):
        """Test password strength validation."""
        from app.utils.password_utils import is_password_strong

        # Test strong password
        strong_password = "SecurePassword123!"
        is_strong, message = is_password_strong(strong_password)
        assert is_strong is True

        # Test weak passwords
        weak_passwords = [
            "short",  # Too short
            "nouppercase123!",  # No uppercase
            "NOLOWERCASE123!",  # No lowercase
            "NoNumbers!",  # No numbers
            "NoSpecial123",  # No special characters
        ]

        for weak_password in weak_passwords:
            is_strong, message = is_password_strong(weak_password)
            assert is_strong is False
            assert len(message) > 0


class TestValidationService:
    """Test cases for validation service."""

    @pytest.fixture
    def validation_service(self):
        """Create validation service instance."""
        return ValidationService()

    def test_valid_provider_data(self, validation_service, valid_provider_data):
        """Test validation of valid provider data."""
        is_valid, errors = validation_service.validate_provider_data(
            valid_provider_data
        )
        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_email_validation(self, validation_service, valid_provider_data):
        """Test email validation."""
        # Test invalid email format
        invalid_data = valid_provider_data.copy()
        invalid_data["email"] = "invalid-email"

        is_valid, errors = validation_service.validate_provider_data(invalid_data)
        assert is_valid is False
        assert "email" in errors

        # Test disposable email
        invalid_data["email"] = "test@10minutemail.com"
        is_valid, errors = validation_service.validate_provider_data(invalid_data)
        assert is_valid is False
        assert "email" in errors

    def test_invalid_phone_validation(self, validation_service, valid_provider_data):
        """Test phone number validation."""
        invalid_data = valid_provider_data.copy()
        invalid_data["phone_number"] = "invalid-phone"

        is_valid, errors = validation_service.validate_provider_data(invalid_data)
        assert is_valid is False
        assert "phone_number" in errors

    def test_invalid_specialization_validation(
        self, validation_service, valid_provider_data
    ):
        """Test specialization validation."""
        invalid_data = valid_provider_data.copy()
        invalid_data["specialization"] = "InvalidSpecialization"

        is_valid, errors = validation_service.validate_provider_data(invalid_data)
        assert is_valid is False
        assert "specialization" in errors

    def test_invalid_license_validation(self, validation_service, valid_provider_data):
        """Test license number validation."""
        invalid_data = valid_provider_data.copy()
        invalid_data["license_number"] = "MD@#$%^&*()"

        is_valid, errors = validation_service.validate_provider_data(invalid_data)
        assert is_valid is False
        assert "license_number" in errors

    def test_invalid_years_experience_validation(
        self, validation_service, valid_provider_data
    ):
        """Test years of experience validation."""
        # Test negative years
        invalid_data = valid_provider_data.copy()
        invalid_data["years_of_experience"] = -5

        is_valid, errors = validation_service.validate_provider_data(invalid_data)
        assert is_valid is False
        assert "years_of_experience" in errors

        # Test too many years
        invalid_data["years_of_experience"] = 60

        is_valid, errors = validation_service.validate_provider_data(invalid_data)
        assert is_valid is False
        assert "years_of_experience" in errors

    def test_invalid_clinic_address_validation(
        self, validation_service, valid_provider_data
    ):
        """Test clinic address validation."""
        invalid_data = valid_provider_data.copy()
        invalid_data["clinic_address"] = {
            "street": "",  # Empty street
            "city": "New York",
            "state": "NY",
            "zip": "invalid-zip",  # Invalid ZIP
        }

        is_valid, errors = validation_service.validate_provider_data(invalid_data)
        assert is_valid is False
        assert "clinic_address" in errors


class TestEmailVerification:
    """Test cases for email verification functionality."""

    def test_email_verification_success(self):
        """Test successful email verification."""
        with patch(
            "app.controllers.provider_controller.verify_token"
        ) as mock_verify_token:
            # Mock valid token
            mock_verify_token.return_value = {
                "provider_id": "test-uuid-123",
                "email": "john.doe@clinic.com",
                "type": "email_verification",
            }

            with patch(
                "app.controllers.provider_controller.ProviderService"
            ) as mock_service:
                # Mock provider data
                mock_service_instance = Mock()
                mock_service_instance.get_provider_by_id.return_value = {
                    "id": "test-uuid-123",
                    "email": "john.doe@clinic.com",
                    "verification_status": "pending",
                    "first_name": "John",
                    "last_name": "Doe",
                }
                mock_service_instance.update_verification_status.return_value = True
                mock_service.return_value = mock_service_instance

                response = client.get("/api/v1/provider/verify?token=valid-token")

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["verification_status"] == "verified"

    def test_email_verification_invalid_token(self):
        """Test email verification with invalid token."""
        with patch(
            "app.controllers.provider_controller.verify_token"
        ) as mock_verify_token:
            # Mock invalid token
            mock_verify_token.return_value = None

            response = client.get("/api/v1/provider/verify?token=invalid-token")

            assert response.status_code == 400
            data = response.json()
            assert data["success"] is False
            assert "Invalid or expired" in data["message"]

    def test_email_verification_wrong_token_type(self):
        """Test email verification with wrong token type."""
        with patch(
            "app.controllers.provider_controller.verify_token"
        ) as mock_verify_token:
            # Mock token with wrong type
            mock_verify_token.return_value = {
                "provider_id": "test-uuid-123",
                "email": "john.doe@clinic.com",
                "type": "wrong_type",
            }

            response = client.get("/api/v1/provider/verify?token=wrong-type-token")

            assert response.status_code == 400
            data = response.json()
            assert data["success"] is False
            assert "Invalid token type" in data["message"]

    def test_email_verification_already_verified(self):
        """Test email verification for already verified provider."""
        with patch(
            "app.controllers.provider_controller.verify_token"
        ) as mock_verify_token:
            # Mock valid token
            mock_verify_token.return_value = {
                "provider_id": "test-uuid-123",
                "email": "john.doe@clinic.com",
                "type": "email_verification",
            }

            with patch(
                "app.controllers.provider_controller.ProviderService"
            ) as mock_service:
                # Mock already verified provider
                mock_service_instance = Mock()
                mock_service_instance.get_provider_by_id.return_value = {
                    "id": "test-uuid-123",
                    "email": "john.doe@clinic.com",
                    "verification_status": "verified",
                    "first_name": "John",
                    "last_name": "Doe",
                }
                mock_service.return_value = mock_service_instance

                response = client.get("/api/v1/provider/verify?token=valid-token")

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "already verified" in data["message"]


class TestHealthEndpoints:
    """Test cases for health check endpoints."""

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
        assert "database_type" in data

    def test_provider_health_endpoint(self):
        """Test provider health check endpoint."""
        response = client.get("/api/v1/provider/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
