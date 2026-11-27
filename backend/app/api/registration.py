import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_requests import read_payload, request_context
from app.application.auth.email_confirmation import (
    InvalidVerificationToken,
    StaleRegistrationConsent,
    confirm_email,
)
from app.application.auth.registration import ConsentVersionMismatch
from app.application.auth.registration_workflow import RegistrationWorkflow
from app.database.session import get_db
from app.infrastructure.email.verification import VerificationDeliveryError
from app.infrastructure.redis.registration_limits import RegistrationRateLimited
from app.infrastructure.security.csrf import CsrfRejected
from app.schemas.auth import RegistrationInput, VerificationResendInput


logger = logging.getLogger(__name__)


class RegistrationAccepted(BaseModel):
    message: str = (
        "Si la solicitud puede procesarse, recibirás las instrucciones por correo. "
        "Si no llegan, puedes solicitar un nuevo enlace."
    )


class VerificationConfirmation(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    token: str = Field(pattern=r"^[A-Za-z0-9_-]{43}$", repr=False)


@contextmanager
def _auth_errors() -> Iterator[None]:
    try:
        yield
    except CsrfRejected:
        raise HTTPException(403, "Invalid request origin or CSRF token") from None
    except RegistrationRateLimited as error:
        raise HTTPException(
            429, "Too many requests", headers={"Retry-After": str(error.retry_after)}
        ) from None
    except RedisError:
        raise HTTPException(503, "Registration temporarily unavailable") from None
    except (ConsentVersionMismatch, StaleRegistrationConsent):
        raise HTTPException(409, "Registration documents must be reviewed again") from None
    except InvalidVerificationToken:
        raise HTTPException(401, "Invalid or expired verification token") from None


async def _send_verification(workflow: RegistrationWorkflow, email: str, token: SecretStr) -> None:
    try:
        await workflow.email_sender.send(email, token)
    except VerificationDeliveryError:
        # Keep the response uniform and leave the pending account eligible for resend.
        logger.warning("Registration verification email delivery failed")


def create_registration_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

    @router.post("/register", status_code=202, response_model=RegistrationAccepted)
    async def register(
        request: Request, background: BackgroundTasks,
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> RegistrationAccepted:
        workflow = request.app.state.registration_workflow
        data = await read_payload(request, RegistrationInput)
        with _auth_errors():
            await workflow.run(
                session, data, request_context(request),
                defer_delivery=lambda email, token: background.add_task(
                    _send_verification, workflow, email, token
                ),
            )
        return RegistrationAccepted()

    @router.post("/email-verification/resend", status_code=202, response_model=RegistrationAccepted)
    async def resend(
        request: Request, background: BackgroundTasks,
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> RegistrationAccepted:
        workflow = request.app.state.registration_workflow
        data = await read_payload(request, VerificationResendInput)
        with _auth_errors():
            await workflow.resend(
                session, data, request_context(request),
                defer_delivery=lambda email, token: background.add_task(
                    _send_verification, workflow, email, token
                ),
            )
        return RegistrationAccepted()

    @router.post("/email-verification/confirm", status_code=204, response_class=Response)
    async def confirm(
        request: Request, session: Annotated[AsyncSession, Depends(get_db)],
    ) -> Response:
        workflow = request.app.state.registration_workflow
        data = await read_payload(request, VerificationConfirmation)
        context = request_context(request)
        with _auth_errors():
            workflow.csrf.require(context.origin, context.csrf_cookie, context.csrf_header)
            await workflow.rate_limiter.require_confirmation(context.client_ip)
            await confirm_email(
                session, data.token, current_versions=workflow.consent_versions,
                environment=workflow.environment,
            )
        return Response(status_code=204)

    return router
