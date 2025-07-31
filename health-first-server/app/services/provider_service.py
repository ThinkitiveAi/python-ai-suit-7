import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from pymongo.collection import Collection
from app.core.database import get_provider_collection, VerificationStatus
from app.core.config import settings
from app.utils.password_utils import hash_password
from app.services.validation_service import ValidationService
from app.services.email_service import EmailService
from loguru import logger


class ProviderService:
    """Service for handling provider registration and management."""

    def __init__(
        self,
        db: Optional[Session] = None,
        mongo_collection: Optional[Collection] = None,
    ):
        self.db = db
        self.mongo_collection = mongo_collection or get_provider_collection()
        self.validation_service = ValidationService(db, mongo_collection)
        self.email_service = EmailService()

    def register_provider(
        self, provider_data: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """
        Register a new provider with comprehensive validation and email verification.

        Args:
            provider_data (Dict[str, Any]): Provider registration data

        Returns:
            Tuple[bool, Dict[str, Any], Optional[str]]: (success, response_data, error_message)
        """
        try:
            # Validate provider data
            is_valid, validation_errors = (
                self.validation_service.validate_provider_data(provider_data)
            )

            if not is_valid:
                return (
                    False,
                    {
                        "success": False,
                        "message": "Validation failed",
                        "errors": validation_errors,
                    },
                    "Validation errors found",
                )

            # Generate unique provider ID
            provider_id = str(uuid.uuid4())

            # Hash password
            password_hash = hash_password(provider_data["password"])

            # Prepare provider data for storage
            provider_record = self._prepare_provider_record(
                provider_data, provider_id, password_hash
            )

            # Save provider to database
            save_success = self._save_provider(provider_record)

            if not save_success:
                return (
                    False,
                    {"success": False, "message": "Failed to save provider data"},
                    "Database save failed",
                )

            # Send verification email
            email_sent = self.email_service.send_provider_verification_email(
                provider_id=provider_id,
                email=provider_data["email"],
                first_name=provider_data["first_name"],
                last_name=provider_data["last_name"],
            )

            # Log email attempt
            self.email_service.log_email_attempt(
                email=provider_data["email"],
                email_type="verification",
                success=email_sent,
                provider_id=provider_id,
            )

            # Prepare success response
            response_data = {
                "success": True,
                "message": "Provider registered successfully. Verification email sent.",
                "data": {
                    "provider_id": provider_id,
                    "email": provider_data["email"],
                    "verification_status": VerificationStatus.PENDING.value,
                },
            }

            logger.info(f"Provider registered successfully: {provider_id}")
            return True, response_data, None

        except Exception as e:
            logger.error(f"Error registering provider: {e}")
            return False, {"success": False, "message": "Internal server error"}, str(e)

    def _prepare_provider_record(
        self, provider_data: Dict[str, Any], provider_id: str, password_hash: str
    ) -> Dict[str, Any]:
        """Prepare provider record for database storage."""
        # Normalize phone number
        phone_number = (
            provider_data["phone_number"]
            .replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )

        # Normalize license number
        license_number = provider_data["license_number"].strip().upper()

        # Prepare clinic address
        clinic_address = provider_data["clinic_address"]

        provider_record = {
            "id": provider_id,
            "first_name": provider_data["first_name"].strip(),
            "last_name": provider_data["last_name"].strip(),
            "email": provider_data["email"].strip().lower(),
            "phone_number": phone_number,
            "password_hash": password_hash,
            "specialization": provider_data["specialization"].strip(),
            "license_number": license_number,
            "years_of_experience": int(provider_data["years_of_experience"]),
            "clinic_street": clinic_address["street"].strip(),
            "clinic_city": clinic_address["city"].strip(),
            "clinic_state": clinic_address["state"].strip(),
            "clinic_zip": clinic_address["zip"].strip(),
            "verification_status": VerificationStatus.PENDING.value,
            "license_document_url": None,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        return provider_record

    def _save_provider(self, provider_record: Dict[str, Any]) -> bool:
        """Save provider record to the appropriate database."""
        try:
            if settings.database_type in ["postgresql", "mysql"]:
                return self._save_to_sql(provider_record)
            elif settings.database_type == "mongodb":
                return self._save_to_mongodb(provider_record)
            else:
                logger.error(f"Unsupported database type: {settings.database_type}")
                return False
        except Exception as e:
            logger.error(f"Error saving provider to database: {e}")
            return False

    def _save_to_sql(self, provider_record: Dict[str, Any]) -> bool:
        """Save provider to SQL database."""
        try:
            from app.core.database import ProviderSQL

            # Create SQLAlchemy model instance
            provider = ProviderSQL(
                id=provider_record["id"],
                first_name=provider_record["first_name"],
                last_name=provider_record["last_name"],
                email=provider_record["email"],
                phone_number=provider_record["phone_number"],
                password_hash=provider_record["password_hash"],
                specialization=provider_record["specialization"],
                license_number=provider_record["license_number"],
                years_of_experience=provider_record["years_of_experience"],
                clinic_street=provider_record["clinic_street"],
                clinic_city=provider_record["clinic_city"],
                clinic_state=provider_record["clinic_state"],
                clinic_zip=provider_record["clinic_zip"],
                verification_status=VerificationStatus(
                    provider_record["verification_status"]
                ),
                license_document_url=provider_record["license_document_url"],
                is_active=provider_record["is_active"],
            )

            self.db.add(provider)
            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving to SQL database: {e}")
            return False

    def _save_to_mongodb(self, provider_record: Dict[str, Any]) -> bool:
        """Save provider to MongoDB."""
        try:
            # Convert datetime objects to strings for MongoDB
            mongo_record = provider_record.copy()
            mongo_record["created_at"] = provider_record["created_at"].isoformat()
            mongo_record["updated_at"] = provider_record["updated_at"].isoformat()

            # Insert into MongoDB
            result = self.mongo_collection.insert_one(mongo_record)
            return bool(result.inserted_id)

        except Exception as e:
            logger.error(f"Error saving to MongoDB: {e}")
            return False

    def get_provider_by_id(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Get provider by ID."""
        try:
            if settings.database_type in ["postgresql", "mysql"]:
                return self._get_from_sql_by_id(provider_id)
            elif settings.database_type == "mongodb":
                return self._get_from_mongodb_by_id(provider_id)
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting provider by ID: {e}")
            return None

    def _get_from_sql_by_id(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Get provider from SQL database by ID."""
        try:
            from app.core.database import ProviderSQL

            provider = (
                self.db.query(ProviderSQL).filter(ProviderSQL.id == provider_id).first()
            )

            if not provider:
                return None

            return {
                "id": provider.id,
                "first_name": provider.first_name,
                "last_name": provider.last_name,
                "email": provider.email,
                "phone_number": provider.phone_number,
                "specialization": provider.specialization,
                "license_number": provider.license_number,
                "years_of_experience": provider.years_of_experience,
                "clinic_address": {
                    "street": provider.clinic_street,
                    "city": provider.clinic_city,
                    "state": provider.clinic_state,
                    "zip": provider.clinic_zip,
                },
                "verification_status": provider.verification_status.value,
                "is_active": provider.is_active,
                "created_at": provider.created_at,
                "updated_at": provider.updated_at,
            }

        except Exception as e:
            logger.error(f"Error getting from SQL database: {e}")
            return None

    def _get_from_mongodb_by_id(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Get provider from MongoDB by ID."""
        try:
            provider = self.mongo_collection.find_one({"id": provider_id})

            if not provider:
                return None

            # Convert string dates back to datetime objects
            provider["created_at"] = datetime.fromisoformat(provider["created_at"])
            provider["updated_at"] = datetime.fromisoformat(provider["updated_at"])

            # Format clinic address
            provider["clinic_address"] = {
                "street": provider["clinic_street"],
                "city": provider["clinic_city"],
                "state": provider["clinic_state"],
                "zip": provider["clinic_zip"],
            }

            return provider

        except Exception as e:
            logger.error(f"Error getting from MongoDB: {e}")
            return None

    def update_verification_status(
        self, provider_id: str, status: VerificationStatus
    ) -> bool:
        """Update provider verification status."""
        try:
            if settings.database_type in ["postgresql", "mysql"]:
                return self._update_sql_verification_status(provider_id, status)
            elif settings.database_type == "mongodb":
                return self._update_mongodb_verification_status(provider_id, status)
            else:
                return False
        except Exception as e:
            logger.error(f"Error updating verification status: {e}")
            return False

    def _update_sql_verification_status(
        self, provider_id: str, status: VerificationStatus
    ) -> bool:
        """Update verification status in SQL database."""
        try:
            from app.core.database import ProviderSQL

            provider = (
                self.db.query(ProviderSQL).filter(ProviderSQL.id == provider_id).first()
            )
            if not provider:
                return False

            provider.verification_status = status
            provider.updated_at = datetime.utcnow()

            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating SQL verification status: {e}")
            return False

    def _update_mongodb_verification_status(
        self, provider_id: str, status: VerificationStatus
    ) -> bool:
        """Update verification status in MongoDB."""
        try:
            result = self.mongo_collection.update_one(
                {"id": provider_id},
                {
                    "$set": {
                        "verification_status": status.value,
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                },
            )
            return result.modified_count > 0

        except Exception as e:
            logger.error(f"Error updating MongoDB verification status: {e}")
            return False
