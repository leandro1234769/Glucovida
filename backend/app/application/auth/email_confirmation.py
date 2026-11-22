from hashlib import sha256

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.legal.catalog import Environment, current_legal_documents
from app.models import ConsentEvidence, EmailVerificationToken, User
from app.schemas.auth import ConsentVersions


class InvalidVerificationToken(Exception):
    """The token cannot be used to activate this account."""


class StaleRegistrationConsent(Exception):
    """The account requires updated decisions before activation."""


async def confirm_email(
    session: AsyncSession, token: str, *, current_versions: ConsentVersions, environment: Environment
) -> None:
    token_hash = sha256(token.encode("ascii")).digest()
    async with session.begin():
        user_id = await session.scalar(
            select(EmailVerificationToken.user_id).where(
                EmailVerificationToken.token_hash == token_hash
            )
        )
        if user_id is None:
            raise InvalidVerificationToken

        # Resend and confirmation lock the account first, in the same order.
        user = await session.scalar(
            select(User).where(User.id == user_id).with_for_update()
        )
        if user is None or user.account_status != "pending_verification":
            raise InvalidVerificationToken

        now = await session.scalar(select(func.clock_timestamp()))
        consumed_id = await session.scalar(
            update(EmailVerificationToken)
            .where(
                EmailVerificationToken.token_hash == token_hash,
                EmailVerificationToken.user_id == user_id,
                EmailVerificationToken.consumed_at.is_(None),
                EmailVerificationToken.revoked_at.is_(None),
                EmailVerificationToken.issued_at <= now,
                EmailVerificationToken.expires_at > now,
            )
            .values(consumed_at=now)
            .returning(EmailVerificationToken.id)
        )
        if consumed_id is None:
            raise InvalidVerificationToken

        evidence = {
            row.document_kind: row
            for row in await session.scalars(
                select(ConsentEvidence)
                .where(ConsentEvidence.user_id == user_id)
                .distinct(ConsentEvidence.document_kind)
                .order_by(ConsentEvidence.document_kind, ConsentEvidence.id.desc())
            )
        }
        for document in current_legal_documents(current_versions, environment):
            decision = evidence.get(document.kind)
            if (
                decision is None
                or decision.document_version != document.version
                or decision.document_sha256 != document.sha256
                or decision.document_status != document.status
                or (document.kind != "health_data" and not decision.accepted)
            ):
                raise StaleRegistrationConsent

        user.account_status = "active"
        user.email_verified_at = now
        user.updated_at = now
