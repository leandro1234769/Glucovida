import ssl
from datetime import timedelta
from pathlib import Path

from pydantic import EmailStr, Field, PositiveInt, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from redis.asyncio import Redis

from app.application.auth.registration_workflow import RegistrationWorkflow
from app.infrastructure.email.verification import SmtpVerificationSender
from app.infrastructure.redis.registration_limits import RateLimit, RegistrationRateLimiter
from app.infrastructure.security.csrf import CsrfProtection
from app.legal.catalog import Environment, current_legal_documents
from app.schemas.auth import ConsentVersions, DocumentVersion


class RegistrationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GLUCOVIDA_", env_file=".env", extra="ignore", env_ignore_empty=True)

    environment: Environment = "production"
    public_registration_enabled: bool | None = None
    production_release_approved: bool = False
    database_url: SecretStr | None = Field(default=None, validation_alias="DATABASE_URL")
    allowed_origins: frozenset[str]
    csrf_key: SecretStr
    rate_limit_key: SecretStr
    redis_url: SecretStr
    smtp_host: str
    smtp_port: PositiveInt = 465
    smtp_starttls: bool = False
    smtp_sender: EmailStr
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_ca_file: Path | None = None
    verification_page: str
    terms_version: DocumentVersion
    privacy_version: DocumentVersion
    health_data_version: DocumentVersion
    verification_ttl_minutes: PositiveInt
    registration_ip_requests: PositiveInt
    registration_ip_window_seconds: PositiveInt
    registration_email_requests: PositiveInt
    registration_email_window_seconds: PositiveInt

    def consent_versions(self) -> ConsentVersions:
        return ConsentVersions(
            terms_version=self.terms_version, privacy_version=self.privacy_version,
            health_data_version=self.health_data_version,
        )

    def registration_enabled(self) -> bool:
        enabled = self.public_registration_enabled
        if enabled is False or (self.environment == "production" and enabled is None):
            return False
        current_legal_documents(self.consent_versions(), self.environment)
        if self.environment == "production" and (
            not self.production_release_approved
            or self.smtp_host != "smtp-relay.brevo.com"
            or self.smtp_port != 587
            or not self.smtp_starttls
            or self.smtp_ca_file is not None
            or not self.smtp_username
            or not self.smtp_password
            or not self.smtp_password.get_secret_value()
        ):
            raise ValueError("Production registration requires release approval and verified Brevo settings")
        return True

    def csrf_protection(self) -> CsrfProtection:
        return CsrfProtection(
            self.csrf_key.get_secret_value().encode("utf-8"), self.allowed_origins
        )

    def registration_workflow(self, redis: Redis) -> RegistrationWorkflow:
        return RegistrationWorkflow(
            csrf=self.csrf_protection(),
            rate_limiter=RegistrationRateLimiter(
                redis,
                key_secret=self.rate_limit_key.get_secret_value().encode("utf-8"),
                per_ip=RateLimit(
                    self.registration_ip_requests, self.registration_ip_window_seconds
                ),
                per_email=RateLimit(
                    self.registration_email_requests, self.registration_email_window_seconds
                ),
            ),
            email_sender=SmtpVerificationSender(
                host=self.smtp_host, port=self.smtp_port, sender=self.smtp_sender,
                verification_page=self.verification_page,
                username=self.smtp_username, password=self.smtp_password,
                starttls=self.smtp_starttls,
                tls_context=(
                    ssl.create_default_context(cafile=str(self.smtp_ca_file))
                    if self.smtp_ca_file is not None else None
                ),
            ),
            consent_versions=self.consent_versions(),
            environment=self.environment,
            verification_ttl=timedelta(minutes=self.verification_ttl_minutes),
        )
