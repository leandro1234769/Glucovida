import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from psycopg.errors import RaiseException
from sqlalchemy import create_engine, make_url, text
from sqlalchemy.exc import DBAPIError


SESSION_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
SESSION_END = SESSION_START + timedelta(hours=2)
ONE_MINUTE = timedelta(minutes=1)


@pytest.fixture(scope="module")
def engine():
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.fail("Set TEST_DATABASE_URL to the migrated glucovida_test database")

    url = make_url(database_url)
    if url.drivername != "postgresql+psycopg" or url.database != "glucovida_test":
        pytest.fail("TEST_DATABASE_URL must use postgresql+psycopg and glucovida_test")

    engine = create_engine(url)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def connection(engine):
    with engine.connect() as connection:
        if connection.scalar(text("SELECT current_database()")) != "glucovida_test":
            pytest.fail("The connection must point to glucovida_test")
        # Closing the connection rolls back all test data, even after a trigger error.
        yield connection


@pytest.fixture
def session_id(connection):
    user_id = connection.scalar(
        text("""
            INSERT INTO glucovida.users (names, surnames, email, password_hash)
            VALUES ('Test', 'User', :email, 'test-hash')
            RETURNING id
        """),
        {"email": f"{uuid4()}@example.test"},
    )
    return connection.scalar(
        text("""
            INSERT INTO glucovida.auth_sessions (
                user_id, auth_version_at_creation, created_at,
                last_activity_at, absolute_expires_at
            )
            VALUES (:user_id, 1, :created_at, :created_at, :expires_at)
            RETURNING id
        """),
        {"user_id": user_id, "created_at": SESSION_START, "expires_at": SESSION_END},
    )


def insert_refresh_token(connection, session_id, issued_at, expires_at):
    return connection.scalar(
        text("""
            INSERT INTO glucovida.auth_refresh_tokens (
                session_id, token_hash, issued_at, expires_at
            )
            VALUES (:session_id, :token_hash, :issued_at, :expires_at)
            RETURNING id
        """),
        {
            "session_id": session_id,
            "token_hash": os.urandom(32),
            "issued_at": issued_at,
            "expires_at": expires_at,
        },
    )


@pytest.mark.parametrize("operation", ["insert", "update"])
@pytest.mark.parametrize(
    ("issued_at", "expires_at", "message"),
    [
        pytest.param(
            SESSION_START - ONE_MINUTE,
            SESSION_END,
            "Refresh Token cannot be issued before session creation",
            id="before-session-creation",
        ),
        pytest.param(
            SESSION_START,
            SESSION_END + ONE_MINUTE,
            "Refresh Token expiration cannot exceed session absolute expiration",
            id="after-session-expiration",
        ),
    ],
)
def test_rejects_refresh_token_outside_session(
    connection, session_id, operation, issued_at, expires_at, message
):
    if operation == "insert":
        with pytest.raises(DBAPIError) as error:
            insert_refresh_token(connection, session_id, issued_at, expires_at)
    else:
        token_id = insert_refresh_token(connection, session_id, SESSION_START, SESSION_END)
        with pytest.raises(DBAPIError) as error:
            connection.execute(
                text("""
                    UPDATE glucovida.auth_refresh_tokens
                    SET issued_at = :issued_at, expires_at = :expires_at
                    WHERE id = :id
                """),
                {"issued_at": issued_at, "expires_at": expires_at, "id": token_id},
            )

    assert isinstance(error.value.orig, RaiseException)
    assert error.value.orig.diag.message_primary == message


@pytest.mark.parametrize(
    ("column", "new_value", "message"),
    [
        (
            "created_at",
            SESSION_START - ONE_MINUTE,
            "Session creation timestamp cannot be modified",
        ),
        (
            "absolute_expires_at",
            SESSION_END + ONE_MINUTE,
            "Session absolute expiration cannot be modified",
        ),
    ],
)
def test_rejects_changes_to_session_timestamps(
    connection, session_id, column, new_value, message
):
    with pytest.raises(DBAPIError) as error:
        connection.execute(
            text(f"UPDATE glucovida.auth_sessions SET {column} = :value WHERE id = :id"),
            {"value": new_value, "id": session_id},
        )

    assert isinstance(error.value.orig, RaiseException)
    assert error.value.orig.diag.message_primary == message
