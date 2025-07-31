from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Text,
    Enum,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from pymongo import MongoClient
from typing import Optional, Union
import uuid
from datetime import datetime
import enum

from .config import settings

# SQLAlchemy setup for relational databases
if settings.database_type in ["postgresql", "mysql"]:
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
else:
    Base = None
    SessionLocal = None

# MongoDB setup
if settings.database_type == "mongodb":
    if settings.mongodb_url:
        mongo_client = MongoClient(settings.mongodb_url)
    else:
        mongo_client = MongoClient()
    mongo_db = mongo_client[settings.mongodb_database]
else:
    mongo_client = None
    mongo_db = None


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


# SQLAlchemy Model for relational databases
class ProviderSQL(Base):
    __tablename__ = "providers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    specialization = Column(String(100), nullable=False)
    license_number = Column(String(50), unique=True, nullable=False, index=True)
    years_of_experience = Column(Integer, nullable=False)
    clinic_street = Column(String(200), nullable=False)
    clinic_city = Column(String(100), nullable=False)
    clinic_state = Column(String(50), nullable=False)
    clinic_zip = Column(String(20), nullable=False)
    verification_status = Column(
        Enum(VerificationStatus), default=VerificationStatus.PENDING
    )
    license_document_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)


class RefreshTokenSQL(Base):
    __tablename__ = "refresh_tokens"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String(36), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    last_used_at = Column(DateTime, nullable=True)


# Database dependency
def get_db():
    if settings.database_type in ["postgresql", "mysql"]:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    else:
        yield None


# MongoDB collection
def get_provider_collection():
    if settings.database_type == "mongodb" and mongo_db:
        return mongo_db.providers
    return None


# Create tables for relational databases
def create_tables():
    if Base:
        # Import patient models to ensure they are registered with Base
        from app.models.patient_model import PatientSQL, PatientRefreshTokenSQL

        Base.metadata.create_all(bind=engine)
