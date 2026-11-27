from datetime import timedelta

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.security.access_tokens import AccessClaims
from app.models import AuthSession, User


SESSION_IDLE_TIMEOUT = timedelta(minutes=30)


class SessionExpired(Exception):
    """The persisted session no longer authorizes requests."""


async def touch_session(session: AsyncSession, claims: AccessClaims) -> None:
    now = func.statement_timestamp()
    async with session.begin():
        touched = await session.scalar(
            update(AuthSession).where(
                AuthSession.id == claims.session_id,
                AuthSession.user_id == claims.user_id,
                AuthSession.auth_version_at_creation == claims.auth_version,
                AuthSession.revoked_at.is_(None),
                AuthSession.absolute_expires_at > now,
                AuthSession.last_activity_at > now - SESSION_IDLE_TIMEOUT,
                User.id == AuthSession.user_id,
                User.account_status == "active",
                User.email_verified_at.is_not(None),
                User.auth_version == claims.auth_version,
            )
            .values(last_activity_at=func.greatest(AuthSession.last_activity_at, now))
            .returning(AuthSession.id)
        )
        if touched is None:
            raise SessionExpired
