from fastapi import APIRouter, Response
from pydantic import BaseModel

from app.infrastructure.security.csrf import CSRF_COOKIE, CSRF_MAX_AGE, CsrfProtection


class CsrfResponse(BaseModel):
    csrf_token: str


def create_csrf_router(protection: CsrfProtection) -> APIRouter:
    router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

    @router.get("/csrf", response_model=CsrfResponse)
    def issue_csrf(response: Response) -> CsrfResponse:
        token = protection.issue()
        response.headers["Cache-Control"] = "no-store"
        response.set_cookie(
            CSRF_COOKIE, token, max_age=CSRF_MAX_AGE, path="/",
            secure=True, httponly=False, samesite="strict",
        )
        return CsrfResponse(csrf_token=token)

    return router
