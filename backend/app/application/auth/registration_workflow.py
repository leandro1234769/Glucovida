from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth.registration import DuplicateEmailError, register_user, renew_verification_token
from app.legal.catalog import Environment
from app.infrastructure.email.verification import SmtpVerificationSender
from app.infrastructure.redis.registration_limits import RegistrationRateLimiter
from app.infrastructure.security.csrf import CsrfProtection
from app.schemas.auth import ConsentVersions, RegistrationInput, VerificationResendInput


@dataclass(frozen=True)
class RegistrationContext:
    client_ip: str
    origin: str | None
    csrf_cookie: str | None
    csrf_header: str | None


@dataclass(frozen=True)
class RegistrationWorkflow:
    csrf: CsrfProtection
    rate_limiter: RegistrationRateLimiter
    email_sender: SmtpVerificationSender
    consent_versions: ConsentVersions
    verification_ttl: timedelta
    environment: Environment = "development"

    async def run(
        self, session: AsyncSession, data: RegistrationInput, context: RegistrationContext,
        *, defer_delivery: Callable[[str, SecretStr], None] | None = None,
    ) -> None:
        await self._require_request(context, data.email)
        try:
            result = await register_user(
                session, data,
                verification_ttl=self.verification_ttl,
                current_consent_versions=self.consent_versions,
                environment=self.environment,
            )
        except DuplicateEmailError:
            return

        await self._deliver(data.email, result.verification_token, defer_delivery)


    async def resend(
        self, session: AsyncSession, data: VerificationResendInput, context: RegistrationContext,
        *, defer_delivery: Callable[[str, SecretStr], None] | None = None,
    ) -> None:
        await self._require_request(context, data.email)
        result = await renew_verification_token(
            session, data, verification_ttl=self.verification_ttl
        )
        if result is not None:
            await self._deliver(data.email, result.verification_token, defer_delivery)

    async def _deliver(
        self, email: str, token: SecretStr,
        defer_delivery: Callable[[str, SecretStr], None] | None,
    ) -> None:
        if defer_delivery is None:
            await self.email_sender.send(email, token)
        else:
            defer_delivery(email, token)

    async def _require_request(self, context: RegistrationContext, email: str) -> None:
        self.csrf.require(context.origin, context.csrf_cookie, context.csrf_header)
        await self.rate_limiter.require(context.client_ip, email)
