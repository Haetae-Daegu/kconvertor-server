import re

from flask_bcrypt import Bcrypt
from google.auth import exceptions as google_exceptions
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash

from app.models.user import User
from app.services.user_service import *
from app.database.database import db
from app.security.security import bcrypt

USERNAME_MAX_LENGTH = 150
USERNAME_MIN_LENGTH = 3
AVATAR_URL_MAX_LENGTH = 500


def register_data_user(email: str, username: str, password: str):
    hashed_password = hash_password(password)
    new_user = User(email=email, username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return new_user


def hash_password(password: str) -> str:
    return bcrypt.generate_password_hash(password).decode("utf8")


def check_user_password(user: User, password: str) -> bool:
    """Check a password against the stored one.

    Handles bcrypt hashes, werkzeug hashes and legacy plain-text passwords.
    Returns False for accounts without a password (Google-only).
    """
    if user.password is None:
        return False
    try:
        if user.password.startswith("$2b$") or user.password.startswith("$2y$"):
            return Bcrypt().check_password_hash(user.password, password)
        return check_password_hash(user.password, password)
    except ValueError:
        return user.password == password


class GoogleAuthError(Exception):
    """The Google ID token is invalid, expired or for another audience."""


class GoogleUnavailableError(Exception):
    """Google's signing keys could not be fetched."""


class GoogleAccountConflictError(Exception):
    """The Google account cannot be matched to a user safely."""


def verify_google_token(credential: str, client_id: str) -> dict:
    if not client_id:
        # verify_oauth2_token skips the audience check when it is None.
        raise RuntimeError("GOOGLE_CLIENT_ID is not set")
    try:
        return id_token.verify_oauth2_token(
            credential, google_requests.Request(), client_id
        )
    except google_exceptions.TransportError as error:
        raise GoogleUnavailableError(str(error)) from error
    except (ValueError, google_exceptions.GoogleAuthError) as error:
        raise GoogleAuthError(str(error)) from error


def _is_email_verified(idinfo: dict) -> bool:
    value = idinfo.get("email_verified")
    return value is True or value == "true"


def _username_base(idinfo: dict) -> str:
    email = idinfo.get("email") or ""
    for candidate in (idinfo.get("name"), email.split("@")[0]):
        if candidate:
            base = re.sub(r"\s+", " ", candidate).strip()
            if len(base) >= USERNAME_MIN_LENGTH:
                return base
    return "user"


def unique_username(base: str) -> str:
    """Return base, or base followed by the smallest free number."""
    base = base[:USERNAME_MAX_LENGTH]
    if not User.query.filter_by(username=base).first():
        return base
    suffix = 2
    while True:
        tail = str(suffix)
        candidate = base[: USERNAME_MAX_LENGTH - len(tail)] + tail
        if not User.query.filter_by(username=candidate).first():
            return candidate
        suffix += 1


def google_sign_in(idinfo: dict, max_attempts: int = 3):
    """Find, link or create the user for a verified Google ID token.

    Returns (user, created).
    """
    sub = idinfo["sub"]
    email = idinfo.get("email")
    picture = (idinfo.get("picture") or "")[:AVATAR_URL_MAX_LENGTH] or None

    user = User.query.filter_by(google_sub=sub).first()
    if user:
        return user, False

    if not email:
        raise GoogleAccountConflictError("The Google account has no email address")

    existing = User.query.filter(func.lower(User.email) == email.lower()).first()
    if existing:
        if not _is_email_verified(idinfo):
            raise GoogleAccountConflictError(
                "An account with this email already exists. "
                "Sign in with your password first."
            )
        if existing.google_sub is not None:
            raise GoogleAccountConflictError(
                "This email is linked to another Google account"
            )
        existing.google_sub = sub
        if not existing.avatar_url:
            existing.avatar_url = picture
        db.session.commit()
        return existing, False

    base = _username_base(idinfo)
    for attempt in range(max_attempts):
        user = User(
            username=unique_username(base),
            email=email,
            password=None,
            google_sub=sub,
            auth_provider="google",
            avatar_url=picture,
        )
        db.session.add(user)
        try:
            db.session.commit()
            return user, True
        except IntegrityError:
            # Another request took the username (or signed this account in)
            # between the check and the insert.
            db.session.rollback()
            user = User.query.filter_by(google_sub=sub).first()
            if user:
                return user, False
            if attempt == max_attempts - 1:
                raise
