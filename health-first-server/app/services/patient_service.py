import bcrypt
import jwt
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pymongo.errors import DuplicateKeyError
from loguru import logger

from app.core.config import settings
from app.core.database import get_db, SessionLocal
from app.models.patient_model import (
    get_patient_model,
    get_patient_refresh_token_model,
    PatientSQL,
    PatientRefreshTokenSQL,
)
from app.schemas.patient_schema import (
    PatientRegistrationRequest,
    PatientLoginRequest,
    PatientUpdateRequest,
    Gender,
)
from app.utils.email_service import send_verification_email
from app.utils.sms_service import send_verification_sms


class PatientService:
    """Service class for patient-related operations"""

    def __init__(self):
        self.patient_model = get_patient_model()
        self.refresh_token_model = get_patient_refresh_token_model()

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt with configured salt rounds"""
        salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
        password_hash = bcrypt.hashpw(password.encode("utf-8"), salt)
        return password_hash.decode("utf-8")

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

    def _generate_tokens(self, patient_id: str, email: str) -> Tuple[str, str]:
        """Generate access and refresh tokens"""
        # Access token (30 minutes as per user story)
        access_token_expires = datetime.utcnow() + timedelta(minutes=30)
        access_token_data = {
            "patient_id": patient_id,
            "email": email,
            "role": "patient",
            "exp": access_token_expires,
            "iat": datetime.utcnow(),
        }
        access_token = jwt.encode(
            access_token_data, settings.secret_key, algorithm=settings.algorithm
        )

        # Refresh token (long-lived)
        refresh_token_expires = datetime.utcnow() + timedelta(days=30)
        refresh_token_data = {
            "patient_id": patient_id,
            "email": email,
            "role": "patient",
            "type": "refresh",
            "exp": refresh_token_expires,
            "iat": datetime.utcnow(),
        }
        refresh_token = jwt.encode(
            refresh_token_data, settings.secret_key, algorithm=settings.algorithm
        )

        return access_token, refresh_token

    def _check_account_locked(self, patient_data: Dict[str, Any]) -> bool:
        """Check if account is locked due to too many failed login attempts"""
        locked_until = patient_data.get("locked_until")
        if locked_until:
            if isinstance(locked_until, str):
                locked_until = datetime.fromisoformat(
                    locked_until.replace("Z", "+00:00")
                )
            if datetime.utcnow() < locked_until:
                return True
        return False

    def _lock_account(self, patient_id: str, lock_duration_minutes: int = 30) -> bool:
        """Lock account for specified duration"""
        locked_until = datetime.utcnow() + timedelta(minutes=lock_duration_minutes)

        if settings.database_type == "mongodb":
            return self.patient_model.update_login_attempts(patient_id, 0, locked_until)
        else:
            # For SQL databases
            db = SessionLocal()
            try:
                patient = (
                    db.query(PatientSQL).filter(PatientSQL.id == patient_id).first()
                )
                if patient:
                    patient.failed_login_attempts = 0
                    patient.locked_until = locked_until
                    db.commit()
                    return True
                return False
            except Exception as e:
                logger.error(f"Error locking account: {e}")
                db.rollback()
                return False
            finally:
                db.close()

    def register_patient(
        self, patient_data: PatientRegistrationRequest
    ) -> Dict[str, Any]:
        """Register a new patient with comprehensive validation"""
        try:
            # Check if email already exists
            if self._email_exists(patient_data.email):
                return {
                    "success": False,
                    "message": "Email is already registered",
                    "error_code": "EMAIL_EXISTS",
                }

            # Check if phone number already exists
            if self._phone_exists(patient_data.phone_number):
                return {
                    "success": False,
                    "message": "Phone number is already registered",
                    "error_code": "PHONE_EXISTS",
                }

            # Prepare patient data for database
            db_patient_data = {
                "first_name": patient_data.first_name,
                "last_name": patient_data.last_name,
                "email": patient_data.email.lower(),
                "phone_number": patient_data.phone_number,
                "password_hash": self._hash_password(patient_data.password),
                "date_of_birth": patient_data.date_of_birth,
                "gender": patient_data.gender,
                "address_street": patient_data.address.street,
                "address_city": patient_data.address.city,
                "address_state": patient_data.address.state,
                "address_zip": patient_data.address.zip,
                "medical_history": patient_data.medical_history or [],
            }

            # Add optional fields if provided
            if patient_data.emergency_contact:
                db_patient_data.update(
                    {
                        "emergency_contact_name": patient_data.emergency_contact.name,
                        "emergency_contact_phone": patient_data.emergency_contact.phone,
                        "emergency_contact_relationship": patient_data.emergency_contact.relationship,
                    }
                )

            if patient_data.insurance_info:
                db_patient_data.update(
                    {
                        "insurance_provider": patient_data.insurance_info.provider,
                        "insurance_policy_number": patient_data.insurance_info.policy_number,
                    }
                )

            # Create patient in database
            if settings.database_type == "mongodb":
                patient_id = self.patient_model.create_patient(db_patient_data)
            else:
                # For SQL databases
                db = SessionLocal()
                try:
                    patient = PatientSQL(**db_patient_data)
                    db.add(patient)
                    db.commit()
                    db.refresh(patient)
                    patient_id = patient.id
                except IntegrityError as e:
                    db.rollback()
                    logger.error(f"Database integrity error: {e}")
                    return {
                        "success": False,
                        "message": "Registration failed due to duplicate data",
                        "error_code": "DUPLICATE_DATA",
                    }
                except Exception as e:
                    db.rollback()
                    logger.error(f"Database error during registration: {e}")
                    return {
                        "success": False,
                        "message": "Registration failed",
                        "error_code": "DATABASE_ERROR",
                    }
                finally:
                    db.close()

            # Send verification email
            try:
                send_verification_email(patient_data.email, patient_id)
            except Exception as e:
                logger.error(f"Failed to send verification email: {e}")

            # Send verification SMS
            try:
                send_verification_sms(patient_data.phone_number, patient_id)
            except Exception as e:
                logger.error(f"Failed to send verification SMS: {e}")

            return {
                "success": True,
                "message": "Patient registered successfully. Verification email sent.",
                "data": {
                    "patient_id": patient_id,
                    "email": patient_data.email,
                    "phone_number": patient_data.phone_number,
                    "email_verified": False,
                    "phone_verified": False,
                },
            }

        except Exception as e:
            logger.error(f"Error during patient registration: {e}")
            return {
                "success": False,
                "message": "Registration failed",
                "error_code": "INTERNAL_ERROR",
            }

    def login_patient(self, login_data: PatientLoginRequest) -> Dict[str, Any]:
        """Authenticate patient login"""
        try:
            # Find patient by email
            patient = self._find_patient_by_email(login_data.email)
            if not patient:
                return {
                    "success": False,
                    "message": "Invalid credentials",
                    "error_code": "INVALID_CREDENTIALS",
                }

            # Check if account is active
            if not patient.get("is_active", True):
                return {
                    "success": False,
                    "message": "Account is deactivated",
                    "error_code": "ACCOUNT_DEACTIVATED",
                }

            # Check if account is locked
            if self._check_account_locked(patient):
                return {
                    "success": False,
                    "message": "Account is temporarily locked due to too many failed attempts",
                    "error_code": "ACCOUNT_LOCKED",
                }

            # Verify password
            if not self._verify_password(login_data.password, patient["password_hash"]):
                # Increment failed login attempts
                self._increment_failed_attempts(patient["id"])

                # Lock account if too many failed attempts
                failed_attempts = patient.get("failed_login_attempts", 0) + 1
                if failed_attempts >= 5:
                    self._lock_account(patient["id"])
                    return {
                        "success": False,
                        "message": "Account locked due to too many failed attempts",
                        "error_code": "ACCOUNT_LOCKED",
                    }

                return {
                    "success": False,
                    "message": "Invalid credentials",
                    "error_code": "INVALID_CREDENTIALS",
                }

            # Reset failed login attempts on successful login
            self._reset_failed_attempts(patient["id"])

            # Update last login
            self._update_last_login(patient["id"])

            # Generate tokens
            access_token, refresh_token = self._generate_tokens(
                patient["id"], patient["email"]
            )

            # Store refresh token
            self._store_refresh_token(patient["id"], refresh_token)

            return {
                "success": True,
                "message": "Login successful",
                "data": {
                    "access_token": access_token,
                    "expires_in": 1800,  # 30 minutes in seconds
                    "token_type": "Bearer",
                    "patient": {
                        "id": patient["id"],
                        "first_name": patient["first_name"],
                        "last_name": patient["last_name"],
                        "email": patient["email"],
                        "phone_number": patient["phone_number"],
                        "email_verified": patient.get("email_verified", False),
                        "phone_verified": patient.get("phone_verified", False),
                        "is_active": patient.get("is_active", True),
                    },
                },
            }

        except Exception as e:
            logger.error(f"Error during patient login: {e}")
            return {
                "success": False,
                "message": "Login failed",
                "error_code": "INTERNAL_ERROR",
            }

    def get_patient_profile(self, patient_id: str) -> Dict[str, Any]:
        """Get patient profile information"""
        try:
            patient = self._get_patient_by_id(patient_id)
            if not patient:
                return {
                    "success": False,
                    "message": "Patient not found",
                    "error_code": "PATIENT_NOT_FOUND",
                }

            # Remove sensitive information
            patient.pop("password_hash", None)
            patient.pop("data_encryption_key", None)

            return {
                "success": True,
                "message": "Patient profile retrieved successfully",
                "data": patient,
            }

        except Exception as e:
            logger.error(f"Error retrieving patient profile: {e}")
            return {
                "success": False,
                "message": "Failed to retrieve profile",
                "error_code": "INTERNAL_ERROR",
            }

    def update_patient_profile(
        self, patient_id: str, update_data: PatientUpdateRequest
    ) -> Dict[str, Any]:
        """Update patient profile information"""
        try:
            # Check if patient exists
            patient = self._get_patient_by_id(patient_id)
            if not patient:
                return {
                    "success": False,
                    "message": "Patient not found",
                    "error_code": "PATIENT_NOT_FOUND",
                }

            # Prepare update data
            db_update_data = {}

            if update_data.first_name:
                db_update_data["first_name"] = update_data.first_name
            if update_data.last_name:
                db_update_data["last_name"] = update_data.last_name
            if update_data.phone_number:
                # Check if new phone number is already taken
                if self._phone_exists(update_data.phone_number, exclude_id=patient_id):
                    return {
                        "success": False,
                        "message": "Phone number is already registered",
                        "error_code": "PHONE_EXISTS",
                    }
                db_update_data["phone_number"] = update_data.phone_number
                db_update_data["phone_verified"] = False  # Require re-verification

            if update_data.address:
                db_update_data.update(
                    {
                        "address_street": update_data.address.street,
                        "address_city": update_data.address.city,
                        "address_state": update_data.address.state,
                        "address_zip": update_data.address.zip,
                    }
                )

            if update_data.emergency_contact:
                db_update_data.update(
                    {
                        "emergency_contact_name": update_data.emergency_contact.name,
                        "emergency_contact_phone": update_data.emergency_contact.phone,
                        "emergency_contact_relationship": update_data.emergency_contact.relationship,
                    }
                )

            if update_data.medical_history is not None:
                db_update_data["medical_history"] = update_data.medical_history

            if update_data.insurance_info:
                db_update_data.update(
                    {
                        "insurance_provider": update_data.insurance_info.provider,
                        "insurance_policy_number": update_data.insurance_info.policy_number,
                    }
                )

            # Update patient in database
            if settings.database_type == "mongodb":
                success = self.patient_model.update_patient(patient_id, db_update_data)
            else:
                # For SQL databases
                db = SessionLocal()
                try:
                    patient = (
                        db.query(PatientSQL).filter(PatientSQL.id == patient_id).first()
                    )
                    if patient:
                        for key, value in db_update_data.items():
                            setattr(patient, key, value)
                        db.commit()
                        success = True
                    else:
                        success = False
                except Exception as e:
                    logger.error(f"Database error during profile update: {e}")
                    db.rollback()
                    success = False
                finally:
                    db.close()

            if success:
                return {"success": True, "message": "Profile updated successfully"}
            else:
                return {
                    "success": False,
                    "message": "Failed to update profile",
                    "error_code": "UPDATE_FAILED",
                }

        except Exception as e:
            logger.error(f"Error updating patient profile: {e}")
            return {
                "success": False,
                "message": "Profile update failed",
                "error_code": "INTERNAL_ERROR",
            }

    def logout_patient(self, refresh_token: str) -> Dict[str, Any]:
        """Logout patient by revoking refresh token"""
        try:
            # Revoke refresh token
            if settings.database_type == "mongodb":
                success = self.refresh_token_model.revoke_token(refresh_token)
            else:
                # For SQL databases
                db = SessionLocal()
                try:
                    token = (
                        db.query(PatientRefreshTokenSQL)
                        .filter(PatientRefreshTokenSQL.token_hash == refresh_token)
                        .first()
                    )
                    if token:
                        token.is_revoked = True
                        db.commit()
                        success = True
                    else:
                        success = False
                except Exception as e:
                    logger.error(f"Database error during logout: {e}")
                    db.rollback()
                    success = False
                finally:
                    db.close()

            return {
                "success": success,
                "message": "Logout successful" if success else "Logout failed",
            }

        except Exception as e:
            logger.error(f"Error during patient logout: {e}")
            return {
                "success": False,
                "message": "Logout failed",
                "error_code": "INTERNAL_ERROR",
            }

    # Helper methods
    def _email_exists(self, email: str, exclude_id: Optional[str] = None) -> bool:
        """Check if email already exists"""
        if settings.database_type == "mongodb":
            patient = self.patient_model.get_patient_by_email(email.lower())
        else:
            db = SessionLocal()
            try:
                query = db.query(PatientSQL).filter(PatientSQL.email == email.lower())
                if exclude_id:
                    query = query.filter(PatientSQL.id != exclude_id)
                patient = query.first()
            finally:
                db.close()

        return patient is not None

    def _phone_exists(self, phone: str, exclude_id: Optional[str] = None) -> bool:
        """Check if phone number already exists"""
        if settings.database_type == "mongodb":
            patient = self.patient_model.get_patient_by_phone(phone)
        else:
            db = SessionLocal()
            try:
                query = db.query(PatientSQL).filter(PatientSQL.phone_number == phone)
                if exclude_id:
                    query = query.filter(PatientSQL.id != exclude_id)
                patient = query.first()
            finally:
                db.close()

        return patient is not None

    def _find_patient_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Find patient by email or phone number"""
        # Try email first
        if settings.database_type == "mongodb":
            patient = self.patient_model.get_patient_by_email(identifier.lower())
            if not patient:
                patient = self.patient_model.get_patient_by_phone(identifier)
        else:
            db = SessionLocal()
            try:
                patient = (
                    db.query(PatientSQL)
                    .filter(
                        (PatientSQL.email == identifier.lower())
                        | (PatientSQL.phone_number == identifier)
                    )
                    .first()
                )
                if patient:
                    patient = {
                        "id": patient.id,
                        "first_name": patient.first_name,
                        "last_name": patient.last_name,
                        "email": patient.email,
                        "phone_number": patient.phone_number,
                        "password_hash": patient.password_hash,
                        "email_verified": patient.email_verified,
                        "phone_verified": patient.phone_verified,
                        "is_active": patient.is_active,
                        "failed_login_attempts": patient.failed_login_attempts,
                        "locked_until": patient.locked_until,
                    }
            finally:
                db.close()

        return patient

    def _find_patient_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find patient by email"""
        if settings.database_type == "mongodb":
            patient = self.patient_model.get_patient_by_email(email.lower())
        else:
            db = SessionLocal()
            try:
                patient = (
                    db.query(PatientSQL)
                    .filter(PatientSQL.email == email.lower())
                    .first()
                )
                if patient:
                    patient = {
                        "id": patient.id,
                        "first_name": patient.first_name,
                        "last_name": patient.last_name,
                        "email": patient.email,
                        "phone_number": patient.phone_number,
                        "password_hash": patient.password_hash,
                        "email_verified": patient.email_verified,
                        "phone_verified": patient.phone_verified,
                        "is_active": patient.is_active,
                        "failed_login_attempts": patient.failed_login_attempts,
                        "locked_until": patient.locked_until,
                    }
            finally:
                db.close()

        return patient

    def _get_patient_by_id(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get patient by ID"""
        if settings.database_type == "mongodb":
            return self.patient_model.get_patient_by_id(patient_id)
        else:
            db = SessionLocal()
            try:
                patient = (
                    db.query(PatientSQL).filter(PatientSQL.id == patient_id).first()
                )
                if patient:
                    return {
                        "id": patient.id,
                        "first_name": patient.first_name,
                        "last_name": patient.last_name,
                        "email": patient.email,
                        "phone_number": patient.phone_number,
                        "date_of_birth": patient.date_of_birth,
                        "gender": patient.gender,
                        "address": {
                            "street": patient.address_street,
                            "city": patient.address_city,
                            "state": patient.address_state,
                            "zip": patient.address_zip,
                        },
                        "emergency_contact": {
                            "name": patient.emergency_contact_name,
                            "phone": patient.emergency_contact_phone,
                            "relationship": patient.emergency_contact_relationship,
                        }
                        if patient.emergency_contact_name
                        else None,
                        "medical_history": patient.medical_history or [],
                        "insurance_info": {
                            "provider": patient.insurance_provider,
                            "policy_number": patient.insurance_policy_number,
                        }
                        if patient.insurance_provider
                        else None,
                        "email_verified": patient.email_verified,
                        "phone_verified": patient.phone_verified,
                        "is_active": patient.is_active,
                        "created_at": patient.created_at,
                        "updated_at": patient.updated_at,
                    }
                return None
            finally:
                db.close()

    def _increment_failed_attempts(self, patient_id: str) -> None:
        """Increment failed login attempts"""
        if settings.database_type == "mongodb":
            patient = self.patient_model.get_patient_by_id(patient_id)
            if patient:
                failed_attempts = patient.get("failed_login_attempts", 0) + 1
                self.patient_model.update_login_attempts(patient_id, failed_attempts)
        else:
            db = SessionLocal()
            try:
                patient = (
                    db.query(PatientSQL).filter(PatientSQL.id == patient_id).first()
                )
                if patient:
                    patient.failed_login_attempts += 1
                    db.commit()
            except Exception as e:
                logger.error(f"Error incrementing failed attempts: {e}")
                db.rollback()
            finally:
                db.close()

    def _reset_failed_attempts(self, patient_id: str) -> None:
        """Reset failed login attempts"""
        if settings.database_type == "mongodb":
            self.patient_model.update_login_attempts(patient_id, 0)
        else:
            db = SessionLocal()
            try:
                patient = (
                    db.query(PatientSQL).filter(PatientSQL.id == patient_id).first()
                )
                if patient:
                    patient.failed_login_attempts = 0
                    patient.locked_until = None
                    db.commit()
            except Exception as e:
                logger.error(f"Error resetting failed attempts: {e}")
                db.rollback()
            finally:
                db.close()

    def _update_last_login(self, patient_id: str) -> None:
        """Update last login timestamp"""
        if settings.database_type == "mongodb":
            self.patient_model.update_last_login(patient_id)
        else:
            db = SessionLocal()
            try:
                patient = (
                    db.query(PatientSQL).filter(PatientSQL.id == patient_id).first()
                )
                if patient:
                    patient.last_login = datetime.utcnow()
                    patient.login_count += 1
                    db.commit()
            except Exception as e:
                logger.error(f"Error updating last login: {e}")
                db.rollback()
            finally:
                db.close()

    def _store_refresh_token(self, patient_id: str, refresh_token: str) -> None:
        """Store refresh token in database"""
        expires_at = datetime.utcnow() + timedelta(days=30)

        if settings.database_type == "mongodb":
            self.refresh_token_model.create_refresh_token(
                patient_id, refresh_token, expires_at
            )
        else:
            db = SessionLocal()
            try:
                token = PatientRefreshTokenSQL(
                    patient_id=patient_id,
                    token_hash=refresh_token,
                    expires_at=expires_at,
                )
                db.add(token)
                db.commit()
            except Exception as e:
                logger.error(f"Error storing refresh token: {e}")
                db.rollback()
            finally:
                db.close()
