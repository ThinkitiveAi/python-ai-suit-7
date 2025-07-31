import bcrypt
from app.core.config import settings


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with the configured salt rounds.

    Args:
        password (str): Plain text password

    Returns:
        str: Hashed password
    """
    # Encode password to bytes
    password_bytes = password.encode("utf-8")

    # Generate salt and hash password
    salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
    hashed = bcrypt.hashpw(password_bytes, salt)

    # Return hashed password as string
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        password (str): Plain text password to verify
        hashed_password (str): Hashed password to check against

    Returns:
        bool: True if password matches, False otherwise
    """
    # Encode both password and hash to bytes
    password_bytes = password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")

    # Verify password
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def is_password_strong(password: str) -> tuple[bool, str]:
    """
    Check if a password meets security requirements.

    Args:
        password (str): Password to check

    Returns:
        tuple[bool, str]: (is_strong, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"

    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"

    return True, "Password meets all requirements"
