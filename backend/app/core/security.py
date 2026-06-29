"""
app/core/security.py

JWT creation and verification.
Password hashing (for venue owner accounts).
Table code generation (6-digit, cryptographically random).
"""

import secrets
import string
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


# ── Password hashing ─────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT ───────────────────────────────────────────────────────────────────────
def create_access_token(subject: str, role: str, extra: dict = None) -> str:
    """
    Create a short-lived access token.
    subject : the entity ID (venue_id, user_id, or table_session_id)
    role    : 'venue_owner' | 'venue_staff' | 'guest'
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        **(extra or {}),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT.
    Raises JWTError if the token is invalid or expired.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


# ── Table Code Generation ─────────────────────────────────────────────────────
def generate_table_code(length: int = 6) -> str:
    """
    Generate a cryptographically random numeric code for table sessions.
    Example output: "482176"

    Uses secrets module (not random) — guaranteed to be
    unpredictable even if called millions of times.
    """
    digits = string.digits
    return "".join(secrets.choice(digits) for _ in range(length))


# ── Razorpay Webhook Signature Verification ───────────────────────────────────
import hashlib
import hmac


def verify_razorpay_signature(
    order_id: str, payment_id: str, signature: str
) -> bool:
    """
    Verify that a Razorpay payment webhook is genuine.
    NEVER trust a payment without verifying this first.
    """
    message = f"{order_id}|{payment_id}"
    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
