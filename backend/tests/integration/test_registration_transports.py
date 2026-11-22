import asyncio
import hmac
import os
import ssl
from email import policy
from email.parser import BytesParser
from hashlib import sha256
from http.cookies import SimpleCookie
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

import pytest
import trustme
from aiosmtpd.smtp import SMTP
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy import create_engine, delete, make_url, select, text

from app.infrastructure.security.csrf import CSRF_COOKIE, CSRF_MAX_AGE
from app.main import create_app
from app.models import ConsentEvidence, EmailVerificationToken, User
from app.registration_settings import RegistrationSettings


ORIGIN = "https://app.gluco-test.example.com"


class TestMailbox:
    __test__ = False

    def __init__(self):
        self.attempts = 0
        self.messages = []
        self.rejected_message = None

    async def handle_DATA(self, server, session, envelope):
        self.attempts += 1
        if self.attempts == 1:
            self.rejected_message = envelope.original_content
            return "451 temporary failure"
        self.messages.append(envelope.original_content)
        return "250 queued"


def message_token(content, email):
    message = BytesParser(policy=policy.default).parsebytes(content)
    link = next(
        line for line in message.get_content().splitlines() if line.startswith("https://")
    )
    assert str(message["To"]) == email
    assert not urlsplit(link).query
    return parse_qs(urlsplit(link).fragment)["token"][0]


def test_registration_with_real_redis_and_smtp(tmp_path, monkeypatch):
    redis_url = os.environ.get("TEST_REDIS_URL")
    if not redis_url:
        pytest.skip("Set TEST_REDIS_URL to the dedicated Redis test instance")

    database_url = make_url(os.environ["TEST_DATABASE_URL"])
    assert database_url.drivername == "postgresql+psycopg"
    assert database_url.database == "glucovida_test"

    ca = trustme.CA()
    ca_file = tmp_path / "smtp-ca.pem"
    ca.cert_pem.write_to_path(ca_file)
    server_tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ca.issue_cert("127.0.0.1").configure_cert(server_tls)

    mailbox = TestMailbox()
    client_ip = f"2001:db8::{uuid4().hex[:4]}:{uuid4().hex[:4]}"
    email = f"{uuid4()}@example.com"
    limit_secret = ("test-rate-" + uuid4().hex)
    engine = create_engine(database_url)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT current_database()")) == "glucovida_test"

    def persisted():
        with engine.connect() as connection:
            user = connection.execute(
                select(User.__table__).where(User.email == email)
            ).one()
            evidence_id = connection.scalar(
                select(ConsentEvidence.user_id).where(ConsentEvidence.user_id == user.id)
            )
            tokens = connection.execute(
                select(EmailVerificationToken.__table__).where(
                    EmailVerificationToken.user_id == user.id
                ).order_by(EmailVerificationToken.issued_at)
            ).all()
        assert evidence_id == user.id
        return user, tokens

    async def run():
        loop = asyncio.get_running_loop()
        smtp = await loop.create_server(
            lambda: SMTP(mailbox), "127.0.0.1", 0, ssl=server_tls
        )
        smtp_port = smtp.sockets[0].getsockname()[1]
        environment = {
            "ENVIRONMENT": "test",
            "ALLOWED_ORIGINS": f'["{ORIGIN}"]',
            "CSRF_KEY": "test-csrf-" + uuid4().hex,
            "RATE_LIMIT_KEY": limit_secret,
            "REDIS_URL": redis_url,
            "SMTP_HOST": "127.0.0.1",
            "SMTP_PORT": str(smtp_port),
            "SMTP_STARTTLS": "false",
            "SMTP_SENDER": "noreply@example.com",
            "SMTP_CA_FILE": str(ca_file),
            "VERIFICATION_PAGE": f"{ORIGIN}/verify",
            "TERMS_VERSION": "terms-test-v1",
            "PRIVACY_VERSION": "privacy-test-v1",
            "HEALTH_DATA_VERSION": "health-data-test-v1",
            "VERIFICATION_TTL_MINUTES": "30",
            "REGISTRATION_IP_REQUESTS": "5",
            "REGISTRATION_IP_WINDOW_SECONDS": "60",
            "REGISTRATION_EMAIL_REQUESTS": "2",
            "REGISTRATION_EMAIL_WINDOW_SECONDS": "900",
        }
        for key, value in environment.items():
            monkeypatch.setenv(f"GLUCOVIDA_{key}", value)
        monkeypatch.setenv("DATABASE_URL", database_url.render_as_string(hide_password=False))
        settings = RegistrationSettings(public_registration_enabled=False)

        try:
            async with AsyncClient(
                transport=ASGITransport(app=create_app(settings), client=(client_ip, 3000)),
                base_url="https://api.gluco-test.example.com",
            ) as http:
                assert (await http.post("/api/v1/auth/register")).status_code == 404

            settings = RegistrationSettings(public_registration_enabled=True)
            app = create_app(settings)
            async with (
                app.router.lifespan_context(app),
                Redis.from_url(settings.redis_url.get_secret_value()) as redis,
                AsyncClient(
                    transport=ASGITransport(app=app, client=(client_ip, 3000)),
                    base_url="https://api.gluco-test.example.com",
                ) as http,
            ):
                assert await redis.ping()
                try:
                    prefix = "/api/v1/auth"
                    response = await http.get(f"{prefix}/csrf", headers={"Origin": ORIGIN})
                    assert response.status_code == 200
                    assert response.headers["cache-control"] == "no-store"
                    assert response.headers["access-control-allow-origin"] == ORIGIN
                    assert response.headers["access-control-allow-credentials"] == "true"
                    cookie = SimpleCookie()
                    cookie.load(response.headers["set-cookie"])
                    csrf_token = response.json()["csrf_token"]
                    csrf_cookie = cookie[CSRF_COOKIE]
                    assert csrf_cookie.value == csrf_token
                    assert csrf_cookie["secure"] and not csrf_cookie["httponly"]
                    assert csrf_cookie["path"] == "/" and not csrf_cookie["domain"]
                    assert csrf_cookie["samesite"] == "strict"
                    assert csrf_cookie["max-age"] == str(CSRF_MAX_AGE)

                    headers = {"Origin": ORIGIN, "X-CSRF-Token": csrf_token}
                    data = {
                        "names": "Ana", "surnames": "Garcia", "email": email,
                        "password": "Test-password-123",
                        "consent": {
                            "terms_accepted": True, "privacy_acknowledged": True,
                            "health_data_authorized": False,
                            "terms_version": settings.terms_version,
                            "privacy_version": settings.privacy_version,
                            "health_data_version": settings.health_data_version,
                        },
                    }
                    register_url = f"{prefix}/register"
                    resend_url = f"{prefix}/email-verification/resend"
                    confirm_url = f"{prefix}/email-verification/confirm"
                    assert (await http.post(register_url, content=b"data")).status_code == 415
                    assert (await http.post(register_url, json={"a": "a" * 8192})).status_code == 413
                    invalid = await http.post(register_url, json={"password": "test-secret"})
                    assert invalid.status_code == 400 and "test-secret" not in invalid.text
                    assert (await http.post(register_url, json=data, headers={
                        **headers, "Origin": "https://other.example.com"
                    })).status_code == 403

                    pending = await http.post(register_url, json=data, headers=headers)
                    assert pending.status_code == 202
                    original_user, original_tokens = persisted()
                    assert original_user.account_status == "pending_verification"
                    assert len(original_tokens) == 1
                    assert original_tokens[0].revoked_at is None
                    assert mailbox.attempts == 1 and not mailbox.messages

                    resend = {"email": email.upper()}
                    response = await http.post(resend_url, json=resend, headers=headers)
                    assert response.status_code == 202 and response.json() == pending.json()
                    user, tokens = persisted()
                    assert user.id == original_user.id and len(tokens) == 2
                    assert tokens[0].id == original_tokens[0].id
                    assert tokens[0].revoked_at is not None and tokens[1].revoked_at is None
                    assert mailbox.attempts == 2 and len(mailbox.messages) == 1

                    limited = await http.post(resend_url, json=resend, headers=headers)
                    assert limited.status_code == 429 and int(limited.headers["retry-after"]) > 0

                    old = message_token(mailbox.rejected_message, email)
                    received = message_token(mailbox.messages[0], email)
                    assert tokens[1].token_hash == sha256(received.encode("ascii")).digest()
                    assert (await http.post(
                        confirm_url, json={"token": old}, headers=headers
                    )).status_code == 401
                    assert (await http.post(
                        confirm_url, json={"token": received}, headers=headers
                    )).status_code == 204
                    assert (await http.post(
                        confirm_url, json={"token": received}, headers=headers
                    )).status_code == 401
                    active, used_tokens = persisted()
                    assert active.account_status == "active"
                    assert active.email_verified_at == used_tokens[1].consumed_at
                    assert mailbox.attempts == 2
                finally:
                    email_key = hmac.digest(limit_secret.encode(), email.encode(), "sha256").hex()
                    await redis.delete(
                        f"rl:{{register}}:ip:{client_ip}", f"rl:{{register}}:email:{email_key}",
                        f"rl:{{confirm}}:ip:{client_ip}",
                    )
        finally:
            smtp.close()
            await smtp.wait_closed()

    try:
        with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
            runner.run(run())
    finally:
        try:
            with engine.begin() as connection:
                connection.execute(delete(User).where(User.email == email))
        finally:
            engine.dispose()
