from hashlib import sha256
from re import fullmatch

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth.session_activity import revoke_session
from app.infrastructure.security.access_tokens import AccessClaims
from app.models import AuditEvent, AuthRefreshToken, AuthSession, User


async def logout_session(
    session: AsyncSession, claims: AccessClaims | None, raw_token: str | None,
) -> None:
    if claims is None and (raw_token is None or not fullmatch(r"[A-Za-z0-9_-]{43}", raw_token)):
        return

    async with session.begin():
        token_id = None
        if claims is not None:
            user_id, session_id = claims.user_id, claims.session_id
        else:
            token_hash = sha256(raw_token.encode("ascii")).digest()
            location = (await session.execute(
                select(AuthRefreshToken.id, AuthSession.id, AuthSession.user_id)
                .join(AuthSession, AuthSession.id == AuthRefreshToken.session_id)
                .where(AuthRefreshToken.token_hash == token_hash)
            )).one_or_none()
            if location is None:
                return
            token_id, session_id, user_id = location

        # Match refresh lock order so logout and rotation serialize for this session.
        user = await session.get(User, user_id, with_for_update=True, populate_existing=True)
        target = await session.get(AuthSession, session_id, with_for_update=True, populate_existing=True)
        if (
            user is None or target is None or target.user_id != user_id
            or target.revoked_at is not None or target.auth_version_at_creation != user.auth_version
            or (claims is not None and claims.auth_version != user.auth_version)
        ):
            return

        now = await session.scalar(select(func.clock_timestamp()))
        if token_id is not None:
            token = await session.get(AuthRefreshToken, token_id, populate_existing=True)
            if (
                token is None or token.consumed_at is not None or token.revoked_at is not None
                or not token.issued_at <= now < token.expires_at
            ):
                return

        await revoke_session(session, target, now, reason="logout")
        session.add(AuditEvent(
            user_id=user_id, session_id=session_id, occurred_at=now,
            event_type="logout", outcome="success",
        ))
