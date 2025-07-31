from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import ProviderSQL, RefreshTokenSQL
from app.utils.password_utils import verify_password
from app.utils.jwt_utils import create_access_token, create_refresh_token
from app.core.config import settings
from loguru import logger
import hashlib


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def login(
        self,
        identifier: str,
        password: str,
        remember_me: bool = False,
        client_ip: str = None,
    ):
        # Find provider by email or phone
        provider = (
            self.db.query(ProviderSQL)
            .filter(
                (ProviderSQL.email == identifier)
                | (ProviderSQL.phone_number == identifier)
            )
            .first()
        )
        if not provider:
            self._log_attempt(identifier, client_ip, False, reason="not_found")
            return None, "INVALID_CREDENTIALS"

        # Check if account is locked
        now = datetime.utcnow()
        if provider.locked_until and provider.locked_until > now:
            self._log_attempt(identifier, client_ip, False, reason="locked")
            return None, "ACCOUNT_LOCKED"

        # Check if account is active and verified
        if not provider.is_active or provider.verification_status != "verified":
            self._log_attempt(
                identifier, client_ip, False, reason="inactive_or_unverified"
            )
            return None, "NOT_VERIFIED_OR_INACTIVE"

        # Check password
        if not verify_password(password, provider.password_hash):
            provider.failed_login_attempts += 1
            if provider.failed_login_attempts >= 5:
                provider.locked_until = now + timedelta(minutes=30)
                self.db.commit()
                self._log_attempt(
                    identifier, client_ip, False, reason="locked_after_failed"
                )
                return None, "ACCOUNT_LOCKED"
            self.db.commit()
            self._log_attempt(identifier, client_ip, False, reason="bad_password")
            return None, "INVALID_CREDENTIALS"

        # Reset failed attempts on success
        provider.failed_login_attempts = 0
        provider.locked_until = None
        provider.last_login = now
        provider.login_count = (provider.login_count or 0) + 1
        self.db.commit()

        # JWT payload
        payload = {
            "provider_id": provider.id,
            "email": provider.email,
            "role": "provider",
            "specialization": provider.specialization,
            "verification_status": provider.verification_status,
        }
        access_exp = timedelta(hours=24) if remember_me else timedelta(hours=1)
        refresh_exp = timedelta(days=30) if remember_me else timedelta(days=7)
        access_token, access_expiry = create_access_token(payload, access_exp)
        refresh_token, refresh_expiry = create_refresh_token(payload, refresh_exp)

        # Store refresh token (hashed)
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        refresh_token_obj = RefreshTokenSQL(
            provider_id=provider.id,
            token_hash=token_hash,
            expires_at=refresh_expiry,
            is_revoked=False,
            created_at=now,
            last_used_at=None,
        )
        self.db.add(refresh_token_obj)
        self.db.commit()

        self._log_attempt(identifier, client_ip, True)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": int(access_exp.total_seconds()),
            "token_type": "Bearer",
            "provider": {
                "id": provider.id,
                "first_name": provider.first_name,
                "last_name": provider.last_name,
                "email": provider.email,
                "specialization": provider.specialization,
                "verification_status": provider.verification_status,
                "is_active": provider.is_active,
            },
        }, None

    def _log_attempt(self, identifier, client_ip, success, reason=None):
        logger.info(
            f"Login attempt: identifier={identifier}, ip={client_ip}, success={success}, reason={reason}"
        )
