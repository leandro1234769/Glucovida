import asyncio
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe

import bcrypt
from psycopg.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import EmailVerificationToken, User
from app.schemas.auth import RegistrationInput, RegistrationResult


class DuplicateEmailError(Exception):
    """The normalized email is already registered."""


async def register_user(
    session: AsyncSession,
    registration: RegistrationInput,
    *,
    verification_ttl: timedelta,
) -> RegistrationResult:
    """Create the account and token in a transaction owned by this service."""
    if verification_ttl <= timedelta(0):
        raise ValueError("Verification token lifetime must be positive")

    password_hash = await asyncio.to_thread(
        bcrypt.hashpw,
        registration.password.get_secret_value().encode("utf-8"),
        bcrypt.gensalt(rounds=12),
    )

    try:
        async with session.begin():
            user = User(
                names=registration.names,
                surnames=registration.surnames,
                email=registration.email,
                password_hash=password_hash.decode("ascii"),
                account_status="pending_verification",
            )
            session.add(user)
            await session.flush()

            verification_token = token_urlsafe(32)
            issued_at = datetime.now(timezone.utc)
            session.add(
                EmailVerificationToken(
                    user_id=user.id,
                    token_hash=sha256(verification_token.encode("ascii")).digest(),
                    issued_at=issued_at,
                    expires_at=issued_at + verification_ttl,
                )
            )
            result = RegistrationResult(
                user_id=user.id,
                verification_token=verification_token,
            )
    except IntegrityError as error:
        original = error.orig
        if isinstance(original, UniqueViolation) and original.diag.constraint_name == "uq_users_email":
            raise DuplicateEmailError("Email is already registered") from None
        raise

    return result
