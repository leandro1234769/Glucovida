from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.legal.catalog import Environment, LegalDocument, current_legal_documents
from app.models import ConsentEvidence, User
from app.schemas.auth import ConsentVersions, RegistrationConsentInput


class HealthDataAuthorizationRequired(Exception):
    """The authenticated user lacks authorization for the required text version."""


async def require_health_data_authorization(
    session: AsyncSession, user_id: UUID, *, required_version: str,
    environment: Environment = "production",
) -> None:
    """Require the latest affirmative decision for the active account and environment."""
    expected_status = {"development": "draft", "test": "test", "production": "approved"}[environment]
    decision = await session.scalar(
        select(ConsentEvidence)
        .join(User, User.id == ConsentEvidence.user_id)
        .where(
            User.id == user_id,
            User.account_status == "active",
            ConsentEvidence.document_kind == "health_data",
        )
        .order_by(ConsentEvidence.id.desc())
        .limit(1)
    )
    if (
        decision is None or not decision.accepted
        or decision.document_version != required_version
        or decision.document_status != expected_status
    ):
        raise HealthDataAuthorizationRequired("Health data authorization required")


def append_consent_evidence(
    session: AsyncSession, user_id: UUID, consent: RegistrationConsentInput,
    documents: tuple[LegalDocument, ...], recorded_at: datetime,
) -> None:
    decisions = {
        "terms": consent.terms_accepted,
        "privacy": consent.privacy_acknowledged,
        "health_data": consent.health_data_authorized,
    }
    session.add_all([
        ConsentEvidence(
            user_id=user_id,
            document_kind=document.kind,
            document_version=document.version,
            document_status=document.status,
            document_sha256=document.sha256,
            accepted=decisions[document.kind],
            recorded_at=recorded_at,
        )
        for document in documents
    ])


async def update_account_consent(
    session: AsyncSession, user_id: UUID, consent: RegistrationConsentInput, *,
    current_versions: ConsentVersions, environment: Environment,
) -> None:
    """Append the decisions of an already authenticated account."""
    if any(getattr(consent, field) != value for field, value in current_versions.model_dump().items()):
        raise ValueError("Review the current registration documents")
    documents = current_legal_documents(current_versions, environment)
    async with session.begin():
        active_user_id = await session.scalar(
            select(User.id).where(User.id == user_id, User.account_status == "active").with_for_update()
        )
        if active_user_id is None:
            raise HealthDataAuthorizationRequired("An active account is required")
        now = await session.scalar(select(func.clock_timestamp()))
        append_consent_evidence(session, user_id, consent, documents, now)
