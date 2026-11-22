import asyncio
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID

import bcrypt
from psycopg.errors import UniqueViolation
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth.consent import append_consent_evidence
from app.legal.catalog import Environment, current_legal_documents
from app.models import EmailVerificationToken, User
from app.schemas.auth import ConsentVersions, RegistrationInput, RegistrationResult, VerificationResendInput


class DuplicateEmailError(Exception):
    """The normalized email is already registered."""


class ConsentVersionMismatch(Exception):
    """The submitted decisions refer to a stale document version."""


async def register_user(
    session: AsyncSession,
    registration: RegistrationInput,
    *,
    verification_ttl: timedelta,
    current_consent_versions: ConsentVersions,
    environment: Environment = "development",
) -> RegistrationResult:
    """Create the account and token in a transaction owned by this service."""
    if verification_ttl <= timedelta(0):
        raise ValueError("Verification token lifetime must be positive")

    consent = registration.consent
    if (
        consent.terms_version != current_consent_versions.terms_version
        or consent.privacy_version != current_consent_versions.privacy_version
        or consent.health_data_version != current_consent_versions.health_data_version
    ):
        raise ConsentVersionMismatch("Review the current registration documents")

    documents = current_legal_documents(current_consent_versions, environment)
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

            issued_at = datetime.now(timezone.utc)
            result = _issue_verification_token(session, user.id, issued_at, verification_ttl)
            append_consent_evidence(session, user.id, consent, documents, issued_at)
    except IntegrityError as error:
        original = error.orig
        if isinstance(original, UniqueViolation) and original.diag.constraint_name == "uq_users_email":
            raise DuplicateEmailError("Email is already registered") from None
        raise

    return result


async def renew_verification_token(
    session: AsyncSession,
    request: VerificationResendInput,
    *,
    verification_ttl: timedelta,
) -> RegistrationResult | None:
    """Rotate the link for a pending account without changing its registration."""
    if verification_ttl <= timedelta(0):
        raise ValueError("Verification token lifetime must be positive")

    async with session.begin():
        user_id = await session.scalar(
            select(User.id)
            .where(User.email == request.email, User.account_status == "pending_verification")
            .with_for_update()
        )
        if user_id is None:
            return None

        issued_at = datetime.now(timezone.utc)
        await session.execute(
            update(EmailVerificationToken)
            .where(
                EmailVerificationToken.user_id == user_id,
                EmailVerificationToken.consumed_at.is_(None),
                EmailVerificationToken.revoked_at.is_(None),
            )
            .values(revoked_at=issued_at)
        )
        return _issue_verification_token(session, user_id, issued_at, verification_ttl)


def _issue_verification_token(
    session: AsyncSession, user_id: UUID, issued_at: datetime, verification_ttl: timedelta
) -> RegistrationResult:
    raw_token = token_urlsafe(32)
    session.add(
        EmailVerificationToken(
            user_id=user_id,
            token_hash=sha256(raw_token.encode("ascii")).digest(),
            issued_at=issued_at,
            expires_at=issued_at + verification_ttl,
        )
    )
    return RegistrationResult(user_id=user_id, verification_token=raw_token)
