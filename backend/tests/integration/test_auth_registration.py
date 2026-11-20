import asyncio
import os
from datetime import timedelta
from hashlib import sha256
from uuid import uuid4

import bcrypt
import pytest
from psycopg.errors import UniqueViolation
from pydantic import ValidationError
from sqlalchemy import create_engine, delete, make_url, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.application.auth import registration
from app.models import EmailVerificationToken, User
from app.schemas.auth import RegistrationInput


VERIFICATION_TTL = timedelta(minutes=30)
PASSWORD = "Test-password-123"


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
                        session, data, verification_ttl=VERIFICATION_TTL
                    )

            try:
                yield engine, lambda data: runner.run(register(data))
            finally:
                runner.run(async_engine.dispose())
    finally:
        engine.dispose()


@pytest.fixture
def emails(database):
    engine, _ = database
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


def registration_input(email):
    return RegistrationInput(
        names="  Ana  ",
        surnames="  Garcia  ",
        email=email,
        password=PASSWORD,
    )


def test_register_persists_pending_user_and_hashed_verification_token(database, emails):
    engine, register = database
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
    engine, register = database
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
    engine, register = database
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
    data = {"names": "Ana", "surnames": "Garcia", "email": "ana@example.com", "password": PASSWORD}
    data[field] = value
    with pytest.raises(ValidationError) as error:
        RegistrationInput.model_validate(data)

    assert error.value.errors(include_input=False)[0]["loc"] == (field,)
