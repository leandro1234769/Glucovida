import pytest

from app.legal.catalog import LegalDocumentsUnavailable, current_legal_documents
from app.main import create_app
from app.registration_settings import RegistrationSettings
from app.schemas.auth import ConsentVersions


DRAFTS = ConsentVersions(
    terms_version="terms-v1.0.0", privacy_version="privacy-v1.0.0",
    health_data_version="health-data-v1.0.0",
)
TESTS = ConsentVersions(
    terms_version="terms-test-v1", privacy_version="privacy-test-v1",
    health_data_version="health-data-test-v1",
)


def settings(environment, documents, **overrides):
    return RegistrationSettings(
        _env_file=None, environment=environment, **documents.model_dump(),
        allowed_origins={"https://app.example.com"}, csrf_key="c" * 32,
        rate_limit_key="r" * 32, redis_url="redis://127.0.0.1:16379/15",
        smtp_host="127.0.0.1", smtp_sender="no-reply@example.com",
        verification_page="https://app.example.com/verify", verification_ttl_minutes=30,
        registration_ip_requests=5, registration_ip_window_seconds=60,
        registration_email_requests=2, registration_email_window_seconds=900,
        **overrides,
    )


def test_only_approved_documents_can_enable_production_registration():
    app = create_app(settings("production", DRAFTS, public_registration_enabled=False))
    assert "/api/v1/auth/register" not in app.openapi()["paths"]
    with pytest.raises(LegalDocumentsUnavailable):
        create_app(settings(
            "production", DRAFTS, public_registration_enabled=True, production_release_approved=True
        ))


@pytest.mark.parametrize(("environment", "versions", "status"), [
    ("development", DRAFTS, "draft"),
    ("test", TESTS, "test"),
])
def test_environment_document_sets_enable_local_registration(environment, versions, status):
    docs = current_legal_documents(versions, environment)
    assert {doc.kind for doc in docs} == {"terms", "privacy", "health_data"}
    assert all(doc.status == status and len(doc.sha256) == 64 for doc in docs)
    assert "/api/v1/auth/register" in create_app(settings(environment, versions)).openapi()["paths"]


@pytest.mark.parametrize(("environment", "versions"), [
    ("development", TESTS), ("test", DRAFTS), ("production", TESTS),
])
def test_documents_are_rejected_outside_their_environment(environment, versions):
    with pytest.raises(LegalDocumentsUnavailable):
        current_legal_documents(versions, environment)
