import asyncio
import os
from datetime import timedelta
from hashlib import sha256
from uuid import uuid4
from unittest.mock import AsyncMock

from fakeredis.aioredis import FakeRedis

import bcrypt
import pytest
from psycopg.errors import UniqueViolation
from pydantic import ValidationError
from sqlalchemy import create_engine, delete, make_url, select, text, update
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.application.auth import consent, login, registration
from app.application.auth.registration_workflow import RegistrationContext, RegistrationWorkflow
from app.infrastructure.redis.registration_limits import RateLimit, RegistrationRateLimiter
from app.infrastructure.security.csrf import CsrfProtection, CsrfRejected
from app.models import AuthRefreshToken, AuthSession, ConsentEvidence, EmailVerificationToken, User
from app.schemas.auth import ConsentVersions, LoginInput, RegistrationInput


VERIFICATION_TTL = timedelta(minutes=30)
PASSWORD = "Test-password-123"
VERSIONS = ConsentVersions(
    terms_version="terms-test-v1", privacy_version="privacy-test-v1",
    health_data_version="health-data-test-v1",
)


@pytest.fixture
def database():
    url = make_url(os.environ["TEST_DATABASE_URL"])
    assert url.drivername == "postgresql+psycopg"
    assert url.database == "glucovida_test"

    engine = create_engine(url)
    async_engine = create_async_engine(url)
    sessions = async_sessionmaker(async_engine)
    try:
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT current_database()")) == "glucovida_test"

        # Psycopg requires a selector event loop on Windows.
        with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
            async def register(data):
                async with sessions() as session:
                    return await registration.register_user(
                        session, data, verification_ttl=VERIFICATION_TTL,
                        current_consent_versions=VERSIONS, environment="test",
                    )

            async def authorize(user_id, version):
                async with sessions() as session:
                    await consent.require_health_data_authorization(
                        session, user_id, required_version=version, environment="test"
                    )

            try:
                yield engine, lambda data: runner.run(register(data)), runner, authorize, sessions
            finally:
                runner.run(async_engine.dispose())
    finally:
        engine.dispose()


@pytest.fixture
def emails(database):
    engine, *_ = database
    addresses = [f"{uuid4()}@example.com" for _ in range(2)]
    with engine.connect() as connection:
        assert connection.scalar(select(User.id).where(User.email.in_(addresses))) is None
    try:
        yield addresses
    finally:
        with engine.begin() as connection:
            user_ids = connection.scalars(
                delete(User).where(User.email.in_(addresses)).returning(User.id)
            ).all()
        with engine.connect() as connection:
            assert connection.scalar(select(User.id).where(User.email.in_(addresses))) is None
            assert connection.scalar(
                select(EmailVerificationToken.id).where(
                    EmailVerificationToken.user_id.in_(user_ids)
                )
            ) is None


def registration_input(email, *, authorized=False, versions=VERSIONS):
    return RegistrationInput(
        names="  Ana  ",
        surnames="  Garcia  ",
        email=email,
        password=PASSWORD,
        consent={
            **versions.model_dump(), "terms_accepted": True, "privacy_acknowledged": True, "health_data_authorized": authorized
        },
    )


def test_register_persists_pending_user_and_hashed_verification_token(database, emails):
    engine, register, *_ = database
    result = register(registration_input(f"  {emails[0].upper()}  "))
    raw_token = result.verification_token.get_secret_value()

    with engine.connect() as connection:
        user = connection.execute(
            select(User.__table__).where(User.id == result.user_id)
        ).one()
        token = connection.execute(
            select(EmailVerificationToken.__table__).where(
                EmailVerificationToken.user_id == result.user_id
            )
        ).one()

        evidence = {
            row.document_kind: row
            for row in connection.execute(
                select(ConsentEvidence.__table__).where(ConsentEvidence.user_id == result.user_id)
            )
        }

    assert (evidence["terms"].document_version, evidence["terms"].accepted) == (
        VERSIONS.terms_version, True
    )
    assert (evidence["privacy"].document_version, evidence["privacy"].accepted) == (
        VERSIONS.privacy_version, True
    )
    assert (evidence["health_data"].document_version, evidence["health_data"].accepted) == (
        VERSIONS.health_data_version, False
    )
    assert all(row.document_status == "test" and row.recorded_at == token.issued_at
               and len(row.document_sha256) == 64 for row in evidence.values())
    assert user.id == result.user_id
    assert (user.names, user.surnames, user.email) == ("Ana", "Garcia", emails[0])
    assert user.account_status == "pending_verification"
    assert user.email_verified_at is None
    assert user.password_hash.split("$")[2] == "12"
    assert bcrypt.checkpw(PASSWORD.encode(), user.password_hash.encode())
    assert token.token_hash == sha256(raw_token.encode("ascii")).digest()
    assert token.expires_at - token.issued_at == VERIFICATION_TTL
    assert token.consumed_at is None
    assert token.revoked_at is None
    assert result.model_dump() == {"user_id": result.user_id}


def test_duplicate_normalized_email_preserves_existing_registration(database, emails):
    engine, register, *_ = database
    result = register(registration_input(emails[0]))

    with pytest.raises(registration.DuplicateEmailError):
        register(registration_input(emails[0].upper()))

    with engine.connect() as connection:
        assert connection.scalars(
            select(User.id).where(User.email == emails[0])
        ).all() == [result.user_id]
        token_hashes = connection.scalars(
            select(EmailVerificationToken.token_hash).where(
                EmailVerificationToken.user_id == result.user_id
            )
        ).all()
    assert token_hashes == [
        sha256(result.verification_token.get_secret_value().encode("ascii")).digest()
    ]


def test_token_insert_failure_rolls_back_new_user(database, emails, monkeypatch):
    engine, register, *_ = database
    first = register(registration_input(emails[0]))
    monkeypatch.setattr(
        registration, "token_urlsafe", lambda _: first.verification_token.get_secret_value()
    )

    with pytest.raises(IntegrityError) as error:
        register(registration_input(emails[1]))

    assert isinstance(error.value.orig, UniqueViolation)
    assert error.value.orig.diag.constraint_name == "uq_email_verification_token_hash"
    with engine.connect() as connection:
        assert connection.scalars(
            select(User.id).where(User.email.in_(emails))
        ).all() == [first.user_id]
        assert connection.scalars(
            select(EmailVerificationToken.user_id).where(
                EmailVerificationToken.token_hash
                == sha256(first.verification_token.get_secret_value().encode("ascii")).digest()
            )
        ).all() == [first.user_id]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("names", "   "),
        ("surnames", "a" * 101),
        ("email", "invalid-email"),
        ("password", "short"),
        ("password", chr(233) * 37),
    ],
)
def test_registration_input_rejects_invalid_values(field, value):
    data = registration_input("ana@example.com").model_dump()
    data[field] = value
    with pytest.raises(ValidationError) as error:
        RegistrationInput.model_validate(data)

    assert error.value.errors(include_input=False)[0]["loc"] == (field,)


def test_health_access_requires_active_account_and_current_affirmative_consent(database, emails):
    engine, register, runner, authorize, _ = database
    accepted = register(registration_input(emails[0], authorized=True))
    declined = register(registration_input(emails[1]))

    with pytest.raises(consent.HealthDataAuthorizationRequired):
        runner.run(authorize(accepted.user_id, VERSIONS.health_data_version))

    with engine.begin() as connection:
        connection.execute(
            update(User).where(User.id.in_([accepted.user_id, declined.user_id])).values(
                account_status="active", email_verified_at=text("now()")
            )
        )

    runner.run(authorize(accepted.user_id, VERSIONS.health_data_version))
    with pytest.raises(consent.HealthDataAuthorizationRequired):
        runner.run(authorize(accepted.user_id, "health-v2"))
    with pytest.raises(consent.HealthDataAuthorizationRequired):
        runner.run(authorize(declined.user_id, VERSIONS.health_data_version))


def test_stale_consent_version_does_not_create_account(database, emails):
    engine, register, *_ = database
    old_versions = VERSIONS.model_copy(update={"privacy_version": "privacy-older"})
    with pytest.raises(registration.ConsentVersionMismatch):
        register(registration_input(emails[0], versions=old_versions))

    with engine.connect() as connection:
        assert connection.scalar(select(User.id).where(User.email == emails[0])) is None


@pytest.mark.parametrize("field,value", [("terms_accepted", False), ("terms_accepted", 1),
                                        ("health_data_authorized", "false")])
def test_consent_requires_explicit_boolean_decisions(field, value):
    data = registration_input("ana@example.com").model_dump()
    data["consent"][field] = value
    with pytest.raises(ValidationError):
        RegistrationInput.model_validate(data)


def test_registration_workflow_checks_csrf_and_sends_only_after_commit(database, emails):
    engine, _, runner, _, sessions = database
    origin = "https://app.example.com"
    csrf = CsrfProtection(b"c" * 32, frozenset({origin}))
    csrf_token = csrf.issue()

    async def verify_delivery(recipient, secret):
        with engine.connect() as connection:
            token_hash = connection.scalar(
                select(EmailVerificationToken.token_hash)
                .join(User, User.id == EmailVerificationToken.user_id)
                .where(User.email == recipient)
            )
        assert token_hash == sha256(secret.get_secret_value().encode("ascii")).digest()

    sender = AsyncMock()
    sender.send.side_effect = verify_delivery

    async def run():
        async with FakeRedis() as redis, sessions() as session:
            workflow = RegistrationWorkflow(
                csrf=csrf,
                rate_limiter=RegistrationRateLimiter(
                    redis, key_secret=b"r" * 32,
                    per_ip=RateLimit(3, 60), per_email=RateLimit(3, 60),
                ),
                email_sender=sender,
                consent_versions=VERSIONS,
                verification_ttl=VERIFICATION_TTL, environment="test",
            )
            data = registration_input(emails[0])
            with pytest.raises(CsrfRejected):
                await workflow.run(session, data, RegistrationContext(
                    "192.0.2.4", "https://other.example.com", csrf_token, csrf_token
                ))
            assert await redis.dbsize() == 0
            sender.send.assert_not_called()

            context = RegistrationContext("192.0.2.4", origin, csrf_token, csrf_token)
            assert await workflow.run(session, data, context) is None
            assert await workflow.run(session, data, context) is None
            sender.send.assert_awaited_once()

    runner.run(run())


def test_consent_history_is_append_only_and_latest_denial_is_enforced(database, emails):
    engine, register, runner, authorize, sessions = database
    email = emails[0]
    user = register(registration_input(email, authorized=True))
    with engine.begin() as connection:
        connection.execute(update(User).where(User.id == user.user_id).values(
            account_status="active", email_verified_at=text("now()")
        ))
    with pytest.raises(DBAPIError, match="Consent evidence is append-only"):
        with engine.begin() as connection:
            connection.execute(update(ConsentEvidence).where(
                ConsentEvidence.user_id == user.user_id
            ).values(accepted=False))

    async def withdraw():
        async with sessions() as session:
            await consent.update_account_consent(
                session, user.user_id, registration_input(email, authorized=False).consent,
                current_versions=VERSIONS, environment="test",
            )

    runner.run(authorize(user.user_id, VERSIONS.health_data_version))
    runner.run(withdraw())
    with pytest.raises(consent.HealthDataAuthorizationRequired):
        runner.run(authorize(user.user_id, VERSIONS.health_data_version))
    with engine.connect() as connection:
        assert connection.scalars(select(ConsentEvidence.accepted).where(
            ConsentEvidence.user_id == user.user_id, ConsentEvidence.document_kind == "health_data",
        ).order_by(ConsentEvidence.id)).all() == [True, False]


def test_login_creates_session_and_refresh_only_after_valid_credentials(database, emails):
    engine, register, runner, _, sessions = database
    email = emails[0]
    user = register(registration_input(email))

    async def authenticate(password):
        async with sessions() as session:
            return await login.login_user(session, LoginInput(email=email.upper(), password=password))

    with pytest.raises(login.InvalidCredentials):
        runner.run(authenticate(PASSWORD))
    with engine.begin() as connection:
        connection.execute(update(User).where(User.id == user.user_id).values(
            account_status="active", email_verified_at=text("now()")
        ))

    for _ in range(5):
        with pytest.raises(login.InvalidCredentials):
            runner.run(authenticate("wrong-password"))
    with pytest.raises(login.InvalidCredentials):
        runner.run(authenticate(PASSWORD))

    with engine.begin() as connection:
        assert connection.scalar(select(AuthSession.id).where(AuthSession.user_id == user.user_id)) is None
        state = connection.execute(select(User.__table__).where(User.id == user.user_id)).one()
        assert state.failed_login_attempts == 5 and state.login_locked_until is not None
        connection.execute(update(User).where(User.id == user.user_id).values(
            login_locked_until=text("now() - interval '1 second'")
        ))

    result = runner.run(authenticate(PASSWORD))
    with engine.connect() as connection:
        session = connection.execute(
            select(AuthSession.__table__).where(AuthSession.id == result.session_id)
        ).one()
        refresh = connection.execute(
            select(AuthRefreshToken.__table__).where(AuthRefreshToken.session_id == session.id)
        ).one()
        state = connection.execute(select(User.__table__).where(User.id == user.user_id)).one()

    assert session.user_id == user.user_id == result.user_id
    assert session.auth_version_at_creation == result.auth_version
    assert session.absolute_expires_at - session.created_at == timedelta(hours=24)
    assert refresh.token_hash == sha256(result.refresh_token.get_secret_value().encode("ascii")).digest()
    assert refresh.expires_at == session.absolute_expires_at
    assert refresh.issued_at == session.created_at
    assert state.failed_login_attempts == 0 and state.login_locked_until is None

def test_http_login_and_inactivity(database, emails, tmp_path):
    import hmac
    import os
    from datetime import timezone
    from http.cookies import SimpleCookie
    from ipaddress import ip_address

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from fastapi import Depends
    from httpx import ASGITransport, AsyncClient
    from pydantic import SecretStr
    from redis.asyncio import Redis

    from app.api.login import require_access_session
    from app.main import create_app
    from app.registration_settings import RegistrationSettings

    redis_url = os.environ.get("TEST_REDIS_URL")
    if not redis_url:
        pytest.skip("Set TEST_REDIS_URL to exercise login over real Redis")

    engine, register, runner, _, _ = database
    email = emails[0]
    user = register(registration_input(email))
    with engine.begin() as connection:
        connection.execute(update(User).where(User.id == user.user_id).values(
            account_status="active", email_verified_at=text("now()")
        ))

    key_path = tmp_path / "test-jwt.pem"
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    key_path.write_bytes(private_key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ))
    origin = "https://app.example.com"
    rate_key = uuid4().hex
    ip = str(ip_address(f"2001:db8::{uuid4().hex[:4]}:{uuid4().hex[:4]}"))
    account_key = hmac.digest(rate_key.encode(), email.encode(), "sha256").hex()
    keys = (f"rl:{{login}}:ip:{ip}", f"rl:{{login}}:email:{account_key}")
    settings = RegistrationSettings(
        _env_file=None, environment="test", public_registration_enabled=False,
        DATABASE_URL=engine.url.render_as_string(hide_password=False),
        allowed_origins={origin}, csrf_key="c" * 32, rate_limit_key=rate_key,
        redis_url=redis_url, jwt_private_key_file=key_path,
        smtp_host="localhost", smtp_sender="no-reply@example.com",
        verification_page="https://app.example.com/verify",
        **VERSIONS.model_dump(), verification_ttl_minutes=30,
        registration_ip_requests=5, registration_ip_window_seconds=60,
        registration_email_requests=2, registration_email_window_seconds=900,
    )
    app = create_app(settings)

    @app.get("/protected")
    async def protected(claims=Depends(require_access_session)):
        return {"user_id": claims.user_id}

    async def run():
        async with (
            app.router.lifespan_context(app),
            Redis.from_url(redis_url) as redis,
            AsyncClient(
                transport=ASGITransport(app=app, client=(ip, 3000)),
                base_url="https://api.example.com",
            ) as http,
        ):
            try:
                csrf = await http.get("/api/v1/auth/csrf", headers={"Origin": origin})
                headers = {"Origin": origin, "X-CSRF-Token": csrf.json()["csrf_token"]}
                url = "/api/v1/auth/login"
                body = {"email": email.upper(), "password": PASSWORD}
                assert (await http.post(url, json=body)).status_code == 403
                wrong = await http.post(url, json={**body, "password": "wrong"}, headers=headers)
                assert wrong.status_code == 401
                for key in keys:
                    seconds, microseconds = await redis.time()
                    now_ms = seconds * 1000 + microseconds // 1000
                    await redis.zadd(key, {str(n): now_ms for n in range(30)})
                    limited = await http.post(url, json=body, headers=headers)
                    assert limited.status_code == 429 and int(limited.headers["Retry-After"]) > 0
                    await redis.delete(key)

                response = await http.post(url, json=body, headers=headers)
                assert response.status_code == 200
                assert response.headers["cache-control"] == "no-store"
                payload = response.json()
                assert set(payload) == {"access_token", "token_type", "expires_in"}
                assert payload["token_type"] == "Bearer" and payload["expires_in"] == 900
                assert response.headers["X-CSRF-Token"] != headers["X-CSRF-Token"]
                cookies = SimpleCookie()
                for value in response.headers.get_list("set-cookie"):
                    cookies.load(value)
                refresh = cookies["__Host-gv_refresh"]
                assert refresh["httponly"] and refresh["secure"] and refresh["samesite"] == "strict"
                assert refresh["path"] == "/" and not refresh["domain"]
                assert 86395 <= int(refresh["max-age"]) <= 86400

                signer = app.state.access_token_signer
                claims = signer.decode(payload["access_token"])
                assert claims.user_id == user.user_id
                access = {"Authorization": f"Bearer {payload['access_token']}"}
                assert (await http.get("/protected", headers=access)).status_code == 200
                with engine.begin() as connection:
                    stored_hash = connection.scalar(select(AuthRefreshToken.token_hash).where(
                        AuthRefreshToken.session_id == claims.session_id
                    ))
                    assert stored_hash == sha256(refresh.value.encode("ascii")).digest()
                    now = connection.scalar(text("SELECT clock_timestamp()"))
                    session_id = uuid4()
                    connection.execute(AuthSession.__table__.insert().values(
                        id=session_id, user_id=user.user_id, auth_version_at_creation=claims.auth_version,
                        created_at=now - timedelta(hours=1),
                        last_activity_at=now - timedelta(minutes=30),
                        absolute_expires_at=now + timedelta(hours=23),
                    ))

                fresh_jwt = signer.issue(login.LoginSession(
                    user.user_id, session_id, claims.auth_version,
                    now.astimezone(timezone.utc), now + timedelta(hours=23), SecretStr("unused"),
                ))
                assert signer.decode(fresh_jwt).session_id == session_id
                denied = await http.get("/protected", headers={"Authorization": f"Bearer {fresh_jwt}"})
                assert denied.status_code == 401
                with engine.connect() as connection:
                    last_activity = connection.scalar(select(AuthSession.last_activity_at).where(
                        AuthSession.id == session_id
                    ))
                assert last_activity == now - timedelta(minutes=30)
            finally:
                await redis.delete(*keys)

    runner.run(run())
