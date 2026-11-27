import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID

import bcrypt
from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuthRefreshToken, AuthSession, User
from app.schemas.auth import LoginInput


# A fixed bcrypt-12 hash keeps unknown-account verification on the same code path.
_DUMMY_HASH = b"$2b$12$fRNqBIe/IPoABar8wehm1ubXoi2O21nN9TnThz.7EPM6HRax1DPcK"
_MAX_FAILED_ATTEMPTS = 5
_LOCK_TIME = timedelta(minutes=15)
_SESSION_LIFETIME = timedelta(hours=24)


class InvalidCredentials(Exception):
    """The supplied credentials cannot start a session."""


@dataclass(frozen=True)
class LoginSession:
    user_id: UUID
    session_id: UUID
    auth_version: int
    created_at: datetime
    expires_at: datetime
    refresh_token: SecretStr = field(repr=False)


async def login_user(session: AsyncSession, credentials: LoginInput) -> LoginSession:
    result = None
    async with session.begin():
        user = await session.scalar(
            select(User).where(User.email == credentials.email).with_for_update()
        )
        eligible = user is not None and user.account_status == "active" and user.email_verified_at is not None
        password_hash = user.password_hash.encode("ascii") if eligible else _DUMMY_HASH
        matches = await asyncio.to_thread(
            bcrypt.checkpw, credentials.password.get_secret_value().encode("utf-8"), password_hash
        )
        if eligible:
            now = await session.scalar(select(func.clock_timestamp()))
            if user.login_locked_until is None or user.login_locked_until <= now:
                if user.login_locked_until is not None:
                    user.login_locked_until = None
                    user.failed_login_attempts = 0

                if matches:
                    user.failed_login_attempts = 0
                    user.last_login_at = now
                    expires_at = now + _SESSION_LIFETIME
                    auth_session = AuthSession(
                        user_id=user.id,
                        auth_version_at_creation=user.auth_version,
                        created_at=now,
                        last_activity_at=now,
                        absolute_expires_at=expires_at,
                    )
                    session.add(auth_session)
                    await session.flush()
                    raw_token = token_urlsafe(32)
                    session.add(AuthRefreshToken(
                        session_id=auth_session.id,
                        token_hash=sha256(raw_token.encode("ascii")).digest(),
                        issued_at=now,
                        expires_at=expires_at,
                    ))
                    result = LoginSession(
                        user.id, auth_session.id, user.auth_version, now, expires_at, SecretStr(raw_token)
                    )
                else:
                    user.failed_login_attempts = min(user.failed_login_attempts + 1, _MAX_FAILED_ATTEMPTS)
                    if user.failed_login_attempts == _MAX_FAILED_ATTEMPTS:
                        user.login_locked_until = now + _LOCK_TIME

    if result is None:
        raise InvalidCredentials("Invalid credentials")
    return result
