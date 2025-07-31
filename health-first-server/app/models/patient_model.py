from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Text,
    Enum,
    Date,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pymongo import MongoClient
from typing import Optional, Union, Dict, Any, List
import uuid
from datetime import datetime, date
import enum
from bson import ObjectId

from app.core.config import settings
from app.schemas.patient_schema import Gender

# Import Base from database module
from app.core.database import Base


class PatientSQL(Base):
    """SQLAlchemy model for Patient in relational databases"""

    __tablename__ = "patients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(Enum(Gender), nullable=False)

    # Address fields
    address_street = Column(String(200), nullable=False)
    address_city = Column(String(100), nullable=False)
    address_state = Column(String(50), nullable=False)
    address_zip = Column(String(20), nullable=False)

    # Emergency contact fields (optional)
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relationship = Column(String(50), nullable=True)

    # Medical and insurance information
    medical_history = Column(JSON, default=list)  # Store as JSON array
    insurance_provider = Column(String(100), nullable=True)
    insurance_policy_number = Column(String(50), nullable=True)

    # Verification and status fields
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Security fields
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)

    # HIPAA compliance fields
    data_encryption_key = Column(
        String(255), nullable=True
    )  # For encrypted sensitive data
    audit_trail_enabled = Column(Boolean, default=True)


class PatientRefreshTokenSQL(Base):
    """SQLAlchemy model for Patient refresh tokens"""

    __tablename__ = "patient_refresh_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    last_used_at = Column(DateTime, nullable=True)


# MongoDB Models (for NoSQL databases)
class PatientMongoDB:
    """MongoDB model for Patient"""

    def __init__(self, collection):
        self.collection = collection

    def create_patient(self, patient_data: Dict[str, Any]) -> str:
        """Create a new patient in MongoDB"""
        patient_id = str(ObjectId())
        patient_data.update(
            {
                "_id": ObjectId(patient_id),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "email_verified": False,
                "phone_verified": False,
                "is_active": True,
                "failed_login_attempts": 0,
                "login_count": 0,
                "audit_trail_enabled": True,
            }
        )

        # Convert date_of_birth to datetime for MongoDB
        if isinstance(patient_data.get("date_of_birth"), date):
            patient_data["date_of_birth"] = datetime.combine(
                patient_data["date_of_birth"], datetime.min.time()
            )

        result = self.collection.insert_one(patient_data)
        return str(result.inserted_id)

    def get_patient_by_id(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get patient by ID"""
        try:
            patient = self.collection.find_one({"_id": ObjectId(patient_id)})
            if patient:
                patient["id"] = str(patient["_id"])
                del patient["_id"]
            return patient
        except Exception:
            return None

    def get_patient_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get patient by email"""
        try:
            patient = self.collection.find_one({"email": email})
            if patient:
                patient["id"] = str(patient["_id"])
                del patient["_id"]
            return patient
        except Exception:
            return None

    def get_patient_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get patient by phone number"""
        try:
            patient = self.collection.find_one({"phone_number": phone})
            if patient:
                patient["id"] = str(patient["_id"])
                del patient["_id"]
            return patient
        except Exception:
            return None

    def update_patient(self, patient_id: str, update_data: Dict[str, Any]) -> bool:
        """Update patient information"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = self.collection.update_one(
                {"_id": ObjectId(patient_id)}, {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception:
            return False

    def delete_patient(self, patient_id: str) -> bool:
        """Soft delete patient (set is_active to False)"""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(patient_id)},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}},
            )
            return result.modified_count > 0
        except Exception:
            return False

    def update_login_attempts(
        self,
        patient_id: str,
        failed_attempts: int,
        locked_until: Optional[datetime] = None,
    ) -> bool:
        """Update failed login attempts"""
        try:
            update_data = {
                "failed_login_attempts": failed_attempts,
                "updated_at": datetime.utcnow(),
            }
            if locked_until:
                update_data["locked_until"] = locked_until

            result = self.collection.update_one(
                {"_id": ObjectId(patient_id)}, {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception:
            return False

    def update_last_login(self, patient_id: str) -> bool:
        """Update last login timestamp and increment login count"""
        try:
            result = self.collection.update_one(
                {"_id": ObjectId(patient_id)},
                {
                    "$set": {
                        "last_login": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    },
                    "$inc": {"login_count": 1},
                },
            )
            return result.modified_count > 0
        except Exception:
            return False


class PatientRefreshTokenMongoDB:
    """MongoDB model for Patient refresh tokens"""

    def __init__(self, collection):
        self.collection = collection

    def create_refresh_token(
        self, patient_id: str, token_hash: str, expires_at: datetime
    ) -> str:
        """Create a new refresh token"""
        token_id = str(ObjectId())
        token_data = {
            "_id": ObjectId(token_id),
            "patient_id": patient_id,
            "token_hash": token_hash,
            "expires_at": expires_at,
            "is_revoked": False,
            "created_at": datetime.utcnow(),
            "last_used_at": None,
        }

        result = self.collection.insert_one(token_data)
        return str(result.inserted_id)

    def get_refresh_token(self, token_hash: str) -> Optional[Dict[str, Any]]:
        """Get refresh token by hash"""
        try:
            token = self.collection.find_one({"token_hash": token_hash})
            if token:
                token["id"] = str(token["_id"])
                del token["_id"]
            return token
        except Exception:
            return None

    def revoke_token(self, token_hash: str) -> bool:
        """Revoke a refresh token"""
        try:
            result = self.collection.update_one(
                {"token_hash": token_hash}, {"$set": {"is_revoked": True}}
            )
            return result.modified_count > 0
        except Exception:
            return False

    def update_last_used(self, token_hash: str) -> bool:
        """Update last used timestamp"""
        try:
            result = self.collection.update_one(
                {"token_hash": token_hash},
                {"$set": {"last_used_at": datetime.utcnow()}},
            )
            return result.modified_count > 0
        except Exception:
            return False

    def cleanup_expired_tokens(self) -> int:
        """Remove expired tokens"""
        try:
            result = self.collection.delete_many(
                {"expires_at": {"$lt": datetime.utcnow()}}
            )
            return result.deleted_count
        except Exception:
            return 0


# Factory function to get the appropriate patient model
def get_patient_model():
    """Get the appropriate patient model based on database type"""
    if settings.database_type == "mongodb":
        from app.core.database import mongo_db

        return PatientMongoDB(mongo_db.patients)
    else:
        # For SQL databases, return the SQLAlchemy model class
        return PatientSQL


def get_patient_refresh_token_model():
    """Get the appropriate refresh token model based on database type"""
    if settings.database_type == "mongodb":
        from app.core.database import mongo_db

        return PatientRefreshTokenMongoDB(mongo_db.patient_refresh_tokens)
    else:
        # For SQL databases, return the SQLAlchemy model class
        return PatientRefreshTokenSQL
