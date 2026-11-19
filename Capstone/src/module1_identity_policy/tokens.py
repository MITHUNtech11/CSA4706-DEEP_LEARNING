"""
JWT Token Engine for Hospital Staff Identity Verification.
Enforces cryptographic signing, tamper verification, and fail-closed validation.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import jwt

from src.config import (
    JWT_SECRET,
    JWT_ALGORITHM,
    JWT_ISSUER,
    JWT_AUDIENCE,
    TOKEN_EXPIRY_MINUTES,
    BREAK_GLASS_EXPIRY_MINUTES
)


class AuthenticationError(Exception):
    """Raised when authentication fails or token is missing/invalid."""
    pass


def issue_token(
    user_id: str,
    name: str,
    role: str,
    level: int,
    department: str,
    assigned_ward: str,
    assigned_patients: list,
    is_break_glass: bool = False,
    break_glass_reason: Optional[str] = None
) -> str:
    """
    Issues a cryptographically signed JWT token carrying verified role and scope attributes.
    """
    now = datetime.now(timezone.utc)
    expiry_minutes = BREAK_GLASS_EXPIRY_MINUTES if is_break_glass else TOKEN_EXPIRY_MINUTES
    exp = now + timedelta(minutes=expiry_minutes)

    payload = {
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "sub": user_id,
        "user_id": user_id,
        "name": name,
        "role": role,
        "level": level,
        "department": department,
        "assigned_ward": assigned_ward,
        "assigned_patients": assigned_patients,
        "is_break_glass": is_break_glass,
        "break_glass_reason": break_glass_reason
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token: Optional[str]) -> Dict[str, Any]:
    """
    Verifies the signed JWT token.
    Fails closed on missing token, expired signature, or tampered payload.
    """
    if not token or not token.strip():
        raise AuthenticationError("FAIL-CLOSED: Missing authentication token. Request refused.")

    # Strip 'Bearer ' if provided
    clean_token = token.replace("Bearer ", "").strip()

    try:
        payload = jwt.decode(
            clean_token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
            options={"require": ["exp", "iss", "aud", "role", "level"]}
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("FAIL-CLOSED: Authentication token has expired. Request refused.")
    except jwt.InvalidSignatureError:
        raise AuthenticationError("FAIL-CLOSED: Cryptographic signature mismatch. Token tampered.")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"FAIL-CLOSED: Invalid token payload: {str(e)}")
