#!/usr/bin/env python3
"""
Simple startup test to verify the application can be imported and configured correctly.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test that all modules can be imported successfully."""
    try:
        print("Testing imports...")

        # Test core imports
        from app.core.config import settings

        print("✓ Core config imported successfully")

        from app.core.database import get_db, get_provider_collection

        print("✓ Database modules imported successfully")

        # Test utility imports
        from app.utils.password_utils import hash_password, verify_password

        print("✓ Password utils imported successfully")

        from app.utils.email_utils import generate_verification_token

        print("✓ Email utils imported successfully")

        # Test service imports
        from app.services.provider_service import ProviderService

        print("✓ Provider service imported successfully")

        from app.services.validation_service import ValidationService

        print("✓ Validation service imported successfully")

        from app.services.email_service import EmailService

        print("✓ Email service imported successfully")

        # Test schema imports
        from app.schemas.provider_schema import ProviderRegistrationRequest

        print("✓ Provider schemas imported successfully")

        # Test middleware imports
        from app.middlewares.rate_limiting import rate_limiter

        print("✓ Rate limiting middleware imported successfully")

        from app.middlewares.validation import validation_middleware

        print("✓ Validation middleware imported successfully")

        # Test controller imports
        from app.controllers.provider_controller import router

        print("✓ Provider controller imported successfully")

        # Test main app import
        from main import app

        print("✓ Main application imported successfully")

        print("\n🎉 All imports successful!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_configuration():
    """Test that configuration is loaded correctly."""
    try:
        print("\nTesting configuration...")

        from app.core.config import settings

        # Test basic settings
        assert settings.app_name == "Provider Registration API"
        assert settings.app_version == "1.0.0"
        assert settings.bcrypt_rounds == 12
        assert settings.rate_limit_requests == 5
        assert settings.rate_limit_window == 3600

        print("✓ Configuration loaded successfully")
        return True

    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def test_password_utils():
    """Test password utility functions."""
    try:
        print("\nTesting password utilities...")

        from app.utils.password_utils import (
            hash_password,
            verify_password,
            is_password_strong,
        )

        # Test password hashing
        password = "SecurePassword123!"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False

        # Test password strength validation
        is_strong, message = is_password_strong(password)
        assert is_strong is True

        is_weak, message = is_password_strong("weak")
        assert is_weak is False

        print("✓ Password utilities working correctly")
        return True

    except Exception as e:
        print(f"❌ Password utilities error: {e}")
        return False


def test_validation_service():
    """Test validation service."""
    try:
        print("\nTesting validation service...")

        from app.services.validation_service import ValidationService

        validation_service = ValidationService()

        # Test valid data
        valid_data = {
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

        is_valid, errors = validation_service.validate_provider_data(valid_data)
        assert is_valid is True
        assert len(errors) == 0

        print("✓ Validation service working correctly")
        return True

    except Exception as e:
        print(f"❌ Validation service error: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting Provider Registration Backend Tests\n")

    tests = [
        test_imports,
        test_configuration,
        test_password_utils,
        test_validation_service,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The application is ready to run.")
        print("\nTo start the application:")
        print("  uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
