"""
Session Management for CineMatch Identity (Visitor-First, Server-Issued, Signed Cookies)
Enforces Rule F8: Server-issued random UUID with signed cm_sid cookie.
"""
import hashlib
import hmac
import uuid
from typing import Optional
from fastapi import Request, Response, HTTPException, status, Depends
from sqlalchemy.orm import Session

from apps.api.config import api_settings
from apps.api.database import get_db
from apps.api.models import User

COOKIE_NAME = "cm_sid"
COOKIE_MAX_AGE = 365 * 24 * 3600  # 1 year

def get_secret_key() -> bytes:
    raw_secret = getattr(api_settings, "secret_key", "cinematch_super_secure_session_secret_key_2026")
    return raw_secret.encode("utf-8")

def sign_session_id(session_id: str) -> str:
    """Signs session_id using HMAC-SHA256."""
    sig = hmac.new(get_secret_key(), session_id.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
    return f"{session_id}.{sig}"

def verify_and_extract_session_id(cookie_val: Optional[str]) -> Optional[str]:
    """Verifies HMAC signature on cookie and returns session_id if valid."""
    if not cookie_val or "." not in cookie_val:
        return None
    session_id, sig = cookie_val.rsplit(".", 1)
    expected_sig = hmac.new(get_secret_key(), session_id.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
    if hmac.compare_digest(sig, expected_sig):
        return session_id
    return None

def set_session_cookie(response: Response, session_id: str) -> None:
    """Sets HttpOnly, SameSite=Lax signed cookie on response."""
    signed_token = sign_session_id(session_id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=signed_token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=getattr(api_settings, "debug", False) is False and getattr(api_settings, "env", "development") == "production",
        path="/"
    )

def get_current_user(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency that returns the current authenticated User model.
    Creates and attaches a new signed session cookie if not present or invalid.
    """
    cookie_val = request.cookies.get(COOKIE_NAME)
    session_id = verify_and_extract_session_id(cookie_val)

    if session_id:
        user = db.query(User).filter(User.id == session_id).first()
        if user:
            return user

    # Create new session
    new_id = f"u_{uuid.uuid4().hex[:16]}"
    username = f"Visitor_{new_id[-4:]}"
    user = User(id=new_id, username=username)
    db.add(user)
    db.commit()
    db.refresh(user)

    set_session_cookie(response, new_id)
    return user
