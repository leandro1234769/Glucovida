from datetime import datetime, timezone
from typing import Annotated, Literal

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_requests import read_payload, request_context
from app.api.csrf import set_csrf_cookie
from app.application.auth.login import InvalidCredentials, LoginSession, login_user
from app.application.auth.refresh import InvalidRefreshToken, rotate_refresh_token
from app.application.auth.session_activity import SessionExpired, touch_session
from app.database.session import get_db
from app.infrastructure.redis.registration_limits import RegistrationRateLimited
from app.infrastructure.security.access_tokens import ACCESS_TOKEN_SECONDS, AccessClaims
from app.infrastructure.security.csrf import CsrfRejected
from app.schemas.auth import LoginInput


REFRESH_COOKIE = "__Host-gv_refresh"
_bearer = HTTPBearer(auto_error=False)


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int = ACCESS_TOKEN_SECONDS


def create_login_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

    @router.post("/login", response_model=LoginResponse)
    async def login(
        request: Request, response: Response, session: Annotated[AsyncSession, Depends(get_db)],
    ) -> LoginResponse:
        data = await read_payload(request, LoginInput)
        context = request_context(request)
        csrf = request.app.state.csrf
        try:
            csrf.require(context.origin, context.csrf_cookie, context.csrf_header)
            await request.app.state.login_limits.require(context.client_ip, data.email)
            credentials = await login_user(session, data)
        except CsrfRejected:
            raise HTTPException(403, "Invalid request origin or CSRF token") from None
        except RegistrationRateLimited as error:
            raise HTTPException(
                429, "Too many requests", headers={"Retry-After": str(error.retry_after)}
            ) from None
        except RedisError:
            raise HTTPException(503, "Authentication temporarily unavailable") from None
        except InvalidCredentials:
            raise HTTPException(401, "Invalid credentials") from None

        return _issue_credentials(request, response, credentials)

    @router.post("/refresh", response_model=LoginResponse)
    async def refresh(
        request: Request, response: Response, session: Annotated[AsyncSession, Depends(get_db)],
    ) -> LoginResponse | Response:
        async for chunk in request.stream():
            if chunk:
                raise HTTPException(400, "Expected an empty request body")
        context = request_context(request)
        limits = request.app.state.login_limits
        try:
            request.app.state.csrf.require(context.origin, context.csrf_cookie, context.csrf_header)
            await limits.require_refresh_ip(context.client_ip)
            credentials = await rotate_refresh_token(
                session, request.cookies.get(REFRESH_COOKIE, ""),
                check_session_limit=limits.require_refresh_session,
            )
        except CsrfRejected:
            raise HTTPException(403, "Invalid request origin or CSRF token") from None
        except RegistrationRateLimited as error:
            raise HTTPException(
                429, "Too many requests", headers={"Retry-After": str(error.retry_after)}
            ) from None
        except RedisError:
            raise HTTPException(503, "Authentication temporarily unavailable") from None
        except InvalidRefreshToken:
            invalid = JSONResponse(
                {"detail": "Invalid or expired session"}, status_code=401,
                headers={"Cache-Control": "no-store"},
            )
            invalid.delete_cookie(REFRESH_COOKIE, path="/", httponly=True, secure=True, samesite="strict")
            return invalid
        return _issue_credentials(request, response, credentials)

    return router


def _issue_credentials(
    request: Request, response: Response, credentials: LoginSession,
) -> LoginResponse:
    access_token = request.app.state.access_token_signer.issue(credentials)
    response.headers["Cache-Control"] = "no-store"
    response.set_cookie(
        REFRESH_COOKIE, credentials.refresh_token.get_secret_value(),
        max_age=max(0, int((credentials.expires_at - datetime.now(timezone.utc)).total_seconds())),
        path="/", httponly=True, secure=True, samesite="strict",
    )
    csrf_token = request.app.state.csrf.issue()
    set_csrf_cookie(response, csrf_token)
    response.headers["X-CSRF-Token"] = csrf_token
    remaining = int(credentials.expires_at.timestamp()) - int(credentials.created_at.timestamp())
    return LoginResponse(access_token=access_token, expires_in=min(ACCESS_TOKEN_SECONDS, remaining))


async def require_access_session(
    request: Request, session: Annotated[AsyncSession, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AccessClaims:
    try:
        if credentials is None:
            raise jwt.InvalidTokenError
        claims = request.app.state.access_token_signer.decode(credentials.credentials)
        await touch_session(session, claims)
    except (jwt.InvalidTokenError, SessionExpired):
        raise HTTPException(
            401, "Invalid or expired session", headers={"WWW-Authenticate": "Bearer"}
        ) from None
    return claims
