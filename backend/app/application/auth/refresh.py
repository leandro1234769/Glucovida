from collections.abc import Awaitable, Callable
from hashlib import sha256
from re import fullmatch
from secrets import token_urlsafe
from uuid import UUID

from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth.login import LoginSession
from app.application.auth.session_activity import SESSION_IDLE_TIMEOUT, revoke_session
from app.models import AuditEvent, AuthRefreshToken, AuthSession, User


class InvalidRefreshToken(Exception):
    """The supplied refresh token cannot renew the session."""


async def rotate_refresh_token(
    session: AsyncSession, raw_token: str, *,
    check_session_limit: Callable[[UUID], Awaitable[None]],
) -> LoginSession:
    if not fullmatch(r"[A-Za-z0-9_-]{43}", raw_token):
        raise InvalidRefreshToken

    token_hash = sha256(raw_token.encode("ascii")).digest()
    async with session.begin():
        location = (await session.execute(
            select(AuthRefreshToken.id, AuthSession.id, AuthSession.user_id)
            .join(AuthSession, AuthSession.id == AuthRefreshToken.session_id)
            .where(AuthRefreshToken.token_hash == token_hash)
        )).one_or_none()
        if location is None:
            raise InvalidRefreshToken

        token_id, session_id, user_id = location
        await check_session_limit(session_id)
        # Lock the account before the session, then re-read token state under the session lock.
        user = await session.get(User, user_id, with_for_update=True, populate_existing=True)
        auth_session = await session.get(AuthSession, session_id, with_for_update=True, populate_existing=True)
        token = await session.get(AuthRefreshToken, token_id, populate_existing=True)
        now = await session.scalar(select(func.clock_timestamp()))

        if (
            user is None or auth_session is None or token is None
            or user.account_status != "active" or user.email_verified_at is None
            or user.auth_version != auth_session.auth_version_at_creation
            or auth_session.revoked_at is not None or auth_session.absolute_expires_at <= now
            or auth_session.last_activity_at <= now - SESSION_IDLE_TIMEOUT
            or token.issued_at > now or token.expires_at <= now or token.revoked_at is not None
        ):
            raise InvalidRefreshToken

        if token.consumed_at is not None:
            await revoke_session(session, auth_session, now, reason="refresh_reuse")
            session.add(AuditEvent(
                user_id=user_id, session_id=session_id, occurred_at=now,
                event_type="refresh_reuse_detected", outcome="security_event",
            ))
        else:
            token.consumed_at = now
            # Release the partial unique index before inserting its new active token.
            await session.flush()
            successor = token_urlsafe(32)
            replacement = AuthRefreshToken(
                session_id=session_id,
                token_hash=sha256(successor.encode("ascii")).digest(),
                issued_at=now, expires_at=auth_session.absolute_expires_at,
            )
            session.add(replacement)
            await session.flush()
            token.replaced_by_token_id = replacement.id
            auth_session.last_activity_at = max(auth_session.last_activity_at, now)
            session.add(AuditEvent(
                user_id=user_id, session_id=session_id, occurred_at=now,
                event_type="refresh_rotated", outcome="success",
            ))
            return LoginSession(
                user_id, session_id, user.auth_version, now,
                auth_session.absolute_expires_at, SecretStr(successor),
            )

    # Commit the security event and revocation before rejecting the request.
    raise InvalidRefreshToken
