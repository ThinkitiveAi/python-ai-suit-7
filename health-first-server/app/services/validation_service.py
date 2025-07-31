import re
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from pymongo.collection import Collection
from app.core.database import get_provider_collection
from app.core.config import settings
from loguru import logger


class ValidationService:
    """Service for validating provider registration data."""

    def __init__(
        self,
        db: Optional[Session] = None,
        mongo_collection: Optional[Collection] = None,
    ):
        self.db = db
        self.mongo_collection = mongo_collection or get_provider_collection()

    def validate_provider_data(self, data: dict) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Comprehensive validation of provider registration data.

        Args:
            data (dict): Provider registration data

        Returns:
            Tuple[bool, Dict[str, List[str]]]: (is_valid, validation_errors)
        """
        errors = {}

        # Validate required fields
        required_fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "password",
            "confirm_password",
            "specialization",
            "license_number",
            "years_of_experience",
            "clinic_address",
        ]

        for field in required_fields:
            if field not in data or not data[field]:
                if field not in errors:
                    errors[field] = []
                errors[field].append(f"{field.replace('_', ' ').title()} is required")

        # Validate individual fields
        self._validate_name(data, errors)
        self._validate_email(data, errors)
        self._validate_phone(data, errors)
        self._validate_password(data, errors)
        self._validate_specialization(data, errors)
        self._validate_license_number(data, errors)
        self._validate_years_experience(data, errors)
        self._validate_clinic_address(data, errors)

        # Check for duplicates
        self._check_duplicates(data, errors)

        return len(errors) == 0, errors

    def _validate_name(self, data: dict, errors: Dict[str, List[str]]):
        """Validate first and last names."""
        if "first_name" in data and data["first_name"]:
            if len(data["first_name"]) < 2:
                if "first_name" not in errors:
                    errors["first_name"] = []
                errors["first_name"].append(
                    "First name must be at least 2 characters long"
                )

            if len(data["first_name"]) > 50:
                if "first_name" not in errors:
                    errors["first_name"] = []
                errors["first_name"].append("First name must not exceed 50 characters")

            if not re.match(r"^[a-zA-Z\s\-\.]+$", data["first_name"]):
                if "first_name" not in errors:
                    errors["first_name"] = []
                errors["first_name"].append(
                    "First name can only contain letters, spaces, hyphens, and periods"
                )

        if "last_name" in data and data["last_name"]:
            if len(data["last_name"]) < 2:
                if "last_name" not in errors:
                    errors["last_name"] = []
                errors["last_name"].append(
                    "Last name must be at least 2 characters long"
                )

            if len(data["last_name"]) > 50:
                if "last_name" not in errors:
                    errors["last_name"] = []
                errors["last_name"].append("Last name must not exceed 50 characters")

            if not re.match(r"^[a-zA-Z\s\-\.]+$", data["last_name"]):
                if "last_name" not in errors:
                    errors["last_name"] = []
                errors["last_name"].append(
                    "Last name can only contain letters, spaces, hyphens, and periods"
                )

    def _validate_email(self, data: dict, errors: Dict[str, List[str]]):
        """Validate email format and uniqueness."""
        if "email" in data and data["email"]:
            email = data["email"].strip().lower()

            # Basic email format validation
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, email):
                if "email" not in errors:
                    errors["email"] = []
                errors["email"].append("Invalid email format")

            # Check for common disposable email domains
            disposable_domains = [
                "10minutemail.com",
                "tempmail.org",
                "guerrillamail.com",
                "mailinator.com",
                "yopmail.com",
                "throwaway.email",
            ]
            domain = email.split("@")[1] if "@" in email else ""
            if domain in disposable_domains:
                if "email" not in errors:
                    errors["email"] = []
                errors["email"].append("Disposable email addresses are not allowed")

    def _validate_phone(self, data: dict, errors: Dict[str, List[str]]):
        """Validate phone number format."""
        if "phone_number" in data and data["phone_number"]:
            phone = (
                data["phone_number"]
                .replace(" ", "")
                .replace("-", "")
                .replace("(", "")
                .replace(")", "")
            )

            # International phone number validation
            phone_pattern = r"^\+?[1-9]\d{1,14}$"
            if not re.match(phone_pattern, phone):
                if "phone_number" not in errors:
                    errors["phone_number"] = []
                errors["phone_number"].append(
                    "Invalid phone number format. Use international format (e.g., +1234567890)"
                )

    def _validate_password(self, data: dict, errors: Dict[str, List[str]]):
        """Validate password strength and confirmation."""
        if "password" in data and data["password"]:
            password = data["password"]

            if len(password) < 8:
                if "password" not in errors:
                    errors["password"] = []
                errors["password"].append("Password must be at least 8 characters long")

            if not any(c.isupper() for c in password):
                if "password" not in errors:
                    errors["password"] = []
                errors["password"].append(
                    "Password must contain at least one uppercase letter"
                )

            if not any(c.islower() for c in password):
                if "password" not in errors:
                    errors["password"] = []
                errors["password"].append(
                    "Password must contain at least one lowercase letter"
                )

            if not any(c.isdigit() for c in password):
                if "password" not in errors:
                    errors["password"] = []
                errors["password"].append("Password must contain at least one number")

            if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
                if "password" not in errors:
                    errors["password"] = []
                errors["password"].append(
                    "Password must contain at least one special character"
                )

        # Validate password confirmation
        if "password" in data and "confirm_password" in data:
            if data["password"] != data["confirm_password"]:
                if "confirm_password" not in errors:
                    errors["confirm_password"] = []
                errors["confirm_password"].append("Passwords do not match")

    def _validate_specialization(self, data: dict, errors: Dict[str, List[str]]):
        """Validate medical specialization."""
        if "specialization" in data and data["specialization"]:
            specialization = data["specialization"].strip()

            if len(specialization) < 3:
                if "specialization" not in errors:
                    errors["specialization"] = []
                errors["specialization"].append(
                    "Specialization must be at least 3 characters long"
                )

            if len(specialization) > 100:
                if "specialization" not in errors:
                    errors["specialization"] = []
                errors["specialization"].append(
                    "Specialization must not exceed 100 characters"
                )

            # Predefined list of valid specializations
            valid_specializations = [
                "Cardiology",
                "Dermatology",
                "Endocrinology",
                "Gastroenterology",
                "General Practice",
                "Internal Medicine",
                "Neurology",
                "Oncology",
                "Orthopedics",
                "Pediatrics",
                "Psychiatry",
                "Radiology",
                "Surgery",
                "Urology",
                "Obstetrics and Gynecology",
                "Emergency Medicine",
                "Family Medicine",
                "Anesthesiology",
                "Pathology",
                "Ophthalmology",
            ]

            if specialization not in valid_specializations:
                if "specialization" not in errors:
                    errors["specialization"] = []
                errors["specialization"].append(
                    f"Specialization must be one of: {', '.join(valid_specializations)}"
                )

    def _validate_license_number(self, data: dict, errors: Dict[str, List[str]]):
        """Validate license number format."""
        if "license_number" in data and data["license_number"]:
            license_num = data["license_number"].strip().upper()

            if not re.match(r"^[A-Za-z0-9]+$", license_num):
                if "license_number" not in errors:
                    errors["license_number"] = []
                errors["license_number"].append("License number must be alphanumeric")

            if len(license_num) < 5:
                if "license_number" not in errors:
                    errors["license_number"] = []
                errors["license_number"].append(
                    "License number must be at least 5 characters long"
                )

    def _validate_years_experience(self, data: dict, errors: Dict[str, List[str]]):
        """Validate years of experience."""
        if "years_of_experience" in data:
            try:
                years = int(data["years_of_experience"])
                if years < 0:
                    if "years_of_experience" not in errors:
                        errors["years_of_experience"] = []
                    errors["years_of_experience"].append(
                        "Years of experience cannot be negative"
                    )
                elif years > 50:
                    if "years_of_experience" not in errors:
                        errors["years_of_experience"] = []
                    errors["years_of_experience"].append(
                        "Years of experience cannot exceed 50"
                    )
            except (ValueError, TypeError):
                if "years_of_experience" not in errors:
                    errors["years_of_experience"] = []
                errors["years_of_experience"].append(
                    "Years of experience must be a valid number"
                )

    def _validate_clinic_address(self, data: dict, errors: Dict[str, List[str]]):
        """Validate clinic address."""
        if "clinic_address" in data and data["clinic_address"]:
            address = data["clinic_address"]

            # Validate street
            if "street" not in address or not address["street"]:
                if "clinic_address" not in errors:
                    errors["clinic_address"] = {}
                if "street" not in errors["clinic_address"]:
                    errors["clinic_address"]["street"] = []
                errors["clinic_address"]["street"].append("Street address is required")
            elif len(address["street"]) > 200:
                if "clinic_address" not in errors:
                    errors["clinic_address"] = {}
                if "street" not in errors["clinic_address"]:
                    errors["clinic_address"]["street"] = []
                errors["clinic_address"]["street"].append(
                    "Street address must not exceed 200 characters"
                )

            # Validate city
            if "city" not in address or not address["city"]:
                if "clinic_address" not in errors:
                    errors["clinic_address"] = {}
                if "city" not in errors["clinic_address"]:
                    errors["clinic_address"]["city"] = []
                errors["clinic_address"]["city"].append("City is required")
            elif len(address["city"]) > 100:
                if "clinic_address" not in errors:
                    errors["clinic_address"] = {}
                if "city" not in errors["clinic_address"]:
                    errors["clinic_address"]["city"] = []
                errors["clinic_address"]["city"].append(
                    "City must not exceed 100 characters"
                )

            # Validate state
            if "state" not in address or not address["state"]:
                if "clinic_address" not in errors:
                    errors["clinic_address"] = {}
                if "state" not in errors["clinic_address"]:
                    errors["clinic_address"]["state"] = []
                errors["clinic_address"]["state"].append("State is required")
            elif len(address["state"]) > 50:
                if "clinic_address" not in errors:
                    errors["clinic_address"] = {}
                if "state" not in errors["clinic_address"]:
                    errors["clinic_address"]["state"] = []
                errors["clinic_address"]["state"].append(
                    "State must not exceed 50 characters"
                )

            # Validate zip code
            if "zip" not in address or not address["zip"]:
                if "clinic_address" not in errors:
                    errors["clinic_address"] = {}
                if "zip" not in errors["clinic_address"]:
                    errors["clinic_address"]["zip"] = []
                errors["clinic_address"]["zip"].append("ZIP code is required")
            else:
                # Basic ZIP code validation (US format)
                zip_pattern = r"^\d{5}(-\d{4})?$"
                if not re.match(zip_pattern, address["zip"]):
                    if "clinic_address" not in errors:
                        errors["clinic_address"] = {}
                    if "zip" not in errors["clinic_address"]:
                        errors["clinic_address"]["zip"] = []
                    errors["clinic_address"]["zip"].append("Invalid ZIP code format")

    def _check_duplicates(self, data: dict, errors: Dict[str, List[str]]):
        """Check for duplicate email and phone number."""
        if "email" in data and data["email"]:
            email = data["email"].strip().lower()

            # Check in SQL database
            if self.db and settings.database_type in ["postgresql", "mysql"]:
                from app.core.database import ProviderSQL

                existing_provider = (
                    self.db.query(ProviderSQL)
                    .filter(ProviderSQL.email == email)
                    .first()
                )
                if existing_provider:
                    if "email" not in errors:
                        errors["email"] = []
                    errors["email"].append("Email address is already registered")

            # Check in MongoDB
            elif self.mongo_collection and settings.database_type == "mongodb":
                existing_provider = self.mongo_collection.find_one({"email": email})
                if existing_provider:
                    if "email" not in errors:
                        errors["email"] = []
                    errors["email"].append("Email address is already registered")

        if "phone_number" in data and data["phone_number"]:
            phone = (
                data["phone_number"]
                .replace(" ", "")
                .replace("-", "")
                .replace("(", "")
                .replace(")", "")
            )

            # Check in SQL database
            if self.db and settings.database_type in ["postgresql", "mysql"]:
                from app.core.database import ProviderSQL

                existing_provider = (
                    self.db.query(ProviderSQL)
                    .filter(ProviderSQL.phone_number == phone)
                    .first()
                )
                if existing_provider:
                    if "phone_number" not in errors:
                        errors["phone_number"] = []
                    errors["phone_number"].append("Phone number is already registered")

            # Check in MongoDB
            elif self.mongo_collection and settings.database_type == "mongodb":
                existing_provider = self.mongo_collection.find_one(
                    {"phone_number": phone}
                )
                if existing_provider:
                    if "phone_number" not in errors:
                        errors["phone_number"] = []
                    errors["phone_number"].append("Phone number is already registered")

        if "license_number" in data and data["license_number"]:
            license_num = data["license_number"].strip().upper()

            # Check in SQL database
            if self.db and settings.database_type in ["postgresql", "mysql"]:
                from app.core.database import ProviderSQL

                existing_provider = (
                    self.db.query(ProviderSQL)
                    .filter(ProviderSQL.license_number == license_num)
                    .first()
                )
                if existing_provider:
                    if "license_number" not in errors:
                        errors["license_number"] = []
                    errors["license_number"].append(
                        "License number is already registered"
                    )

            # Check in MongoDB
            elif self.mongo_collection and settings.database_type == "mongodb":
                existing_provider = self.mongo_collection.find_one(
                    {"license_number": license_num}
                )
                if existing_provider:
                    if "license_number" not in errors:
                        errors["license_number"] = []
                    errors["license_number"].append(
                        "License number is already registered"
                    )
