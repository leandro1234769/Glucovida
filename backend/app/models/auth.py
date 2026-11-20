from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import (
    BYTEA,
    INET,
    JSONB,
    UUID as PG_UUID,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    foreign,
    remote,
)

from app.database.base import Base


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

SCHEMA = "glucovida"


def uuid_v4() -> uuid.UUID:
    """
    Genera identificadores UUID versión 4.

    Se utiliza una función Python para la generación desde ORM.
    PostgreSQL mantiene gen_random_uuid() como respaldo para
    inserciones que no proporcionen explícitamente el ID.
    """
    return uuid.uuid4()


# ============================================================
# 1. USERS
# ============================================================

class User(Base):

    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "length(btrim(names)) > 0",
            name="ck_users_names",
        ),
        CheckConstraint(
            "length(btrim(surnames)) > 0",
            name="ck_users_surnames",
        ),
        CheckConstraint(
            """
            email = lower(email)
            AND email = btrim(email)
            AND length(email) > 0
            """,
            name="ck_users_email",
        ),
        CheckConstraint(
            "length(password_hash) > 0",
            name="ck_users_password_hash",
        ),
        CheckConstraint(
            """
            account_status IN (
                'pending_verification',
                'active',
                'suspended',
                'disabled'
            )
            """,
            name="ck_users_account_status",
        ),
        CheckConstraint(
            """
            account_status <> 'active'
            OR email_verified_at IS NOT NULL
            """,
            name="ck_users_active_verified",
        ),
        CheckConstraint(
            "auth_version >= 1",
            name="ck_users_auth_version",
        ),
        CheckConstraint(
            "failed_login_attempts BETWEEN 0 AND 5",
            name="ck_users_failed_attempts",
        ),
        CheckConstraint(
            """
            login_locked_until IS NULL
            OR failed_login_attempts = 5
            """,
            name="ck_users_login_lock",
        ),
        Index(
            "uq_users_email",
            "email",
            unique=True,
        ),
        Index(
            "idx_users_login_locked_until",
            "login_locked_until",
            postgresql_where=text(
                "login_locked_until IS NOT NULL"
            ),
        ),
        Index(
            "idx_users_account_status",
            "account_status",
        ),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid_v4,
        server_default=text("gen_random_uuid()"),
    )

    names: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    surnames: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(254),
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    account_status: Mapped[str] = mapped_column(
        String(24),
        nullable=False,
        server_default=text("'pending_verification'"),
    )

    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    auth_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("1"),
    )

    password_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    failed_login_attempts: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        server_default=text("0"),
    )

    login_locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relaciones ORM

    sessions: Mapped[list[AuthSession]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    password_recovery_tokens: Mapped[
        list[PasswordRecoveryToken]
    ] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    email_verification_tokens: Mapped[
        list[EmailVerificationToken]
    ] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    audit_events: Mapped[list[AuditEvent]] = relationship(
        back_populates="user",
        passive_deletes="all",
    )


# ============================================================
# 2. AUTH_SESSIONS
# ============================================================

class AuthSession(Base):

    __tablename__ = "auth_sessions"

    __table_args__ = (
        CheckConstraint(
            "auth_version_at_creation >= 1",
            name="ck_auth_sessions_version",
        ),
        CheckConstraint(
            """
            absolute_expires_at > created_at
            AND absolute_expires_at <= created_at + INTERVAL '24 hours'
            """,
            name="ck_auth_sessions_expiration",
        ),
        CheckConstraint(
            """
            last_activity_at >= created_at
            AND last_activity_at <= absolute_expires_at
            """,
            name="ck_auth_sessions_activity",
        ),
        CheckConstraint(
            """
            (
                revoked_at IS NULL
                AND revoke_reason IS NULL
            )
            OR
            (
                revoked_at IS NOT NULL
                AND revoke_reason IS NOT NULL
            )
            """,
            name="ck_auth_sessions_revoked",
        ),
        CheckConstraint(
            """
            revoke_reason IS NULL
            OR revoke_reason IN (
                'logout',
                'password_change',
                'password_recovery',
                'refresh_reuse',
                'admin_action',
                'security_policy',
                'account_disabled'
            )
            """,
            name="ck_auth_sessions_revoke_reason",
        ),
        CheckConstraint(
            """
            revoked_at IS NULL
            OR revoked_at >= created_at
            """,
            name="ck_auth_sessions_revoked_at",
        ),
        Index(
            "idx_auth_sessions_user_revoked",
            "user_id",
            "revoked_at",
        ),
        Index(
            "idx_auth_sessions_active_absolute_expiry",
            "absolute_expires_at",
            postgresql_where=text("revoked_at IS NULL"),
        ),
        Index(
            "idx_auth_sessions_active_last_activity",
            "last_activity_at",
            postgresql_where=text("revoked_at IS NULL"),
        ),
        # El índice de la PK ya permite localizar una sesión
        # por sid. No se agrega un índice redundante (id, av).
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid_v4,
        server_default=text("gen_random_uuid()"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            f"{SCHEMA}.users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    auth_version_at_creation: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # IMPORTANTE:
    # Es una columna normal, no Computed.
    # La aplicación establece su valor como created_at + 24 horas.
    absolute_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    ip_address: Mapped[str | None] = mapped_column(
        INET,
        nullable=True,
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    revoke_reason: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    # Relaciones ORM

    user: Mapped[User] = relationship(
        back_populates="sessions",
    )

    refresh_tokens: Mapped[list[AuthRefreshToken]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    audit_events: Mapped[list[AuditEvent]] = relationship(
        back_populates="session",
        passive_deletes="all",
    )


# ============================================================
# 3. AUTH_REFRESH_TOKENS
# ============================================================

class AuthRefreshToken(Base):

    __tablename__ = "auth_refresh_tokens"

    __table_args__ = (
        CheckConstraint(
            "octet_length(token_hash) = 32",
            name="ck_refresh_token_hash_length",
        ),
        CheckConstraint(
            "expires_at > issued_at",
            name="ck_refresh_token_expiration",
        ),
        CheckConstraint(
            """
            NOT (
                consumed_at IS NOT NULL
                AND revoked_at IS NOT NULL
            )
            """,
            name="ck_refresh_token_state",
        ),
        CheckConstraint(
            """
            consumed_at IS NULL
            OR consumed_at >= issued_at
            """,
            name="ck_refresh_token_consumed_at",
        ),
        CheckConstraint(
            """
            revoked_at IS NULL
            OR revoked_at >= issued_at
            """,
            name="ck_refresh_token_revoked_at",
        ),
        CheckConstraint(
            """
            (
                revoked_at IS NULL
                AND revoke_reason IS NULL
            )
            OR
            (
                revoked_at IS NOT NULL
                AND revoke_reason IS NOT NULL
            )
            """,
            name="ck_refresh_token_revocation_reason",
        ),
        CheckConstraint(
            """
            replaced_by_token_id IS NULL
            OR (
                replaced_by_token_id <> id
                AND consumed_at IS NOT NULL
                AND revoked_at IS NULL
            )
            """,
            name="ck_refresh_token_replacement",
        ),
        UniqueConstraint(
            "session_id",
            "id",
            name="uq_auth_refresh_tokens_session_id_id",
        ),
        ForeignKeyConstraint(
            ["session_id", "replaced_by_token_id"],
            [
                f"{SCHEMA}.auth_refresh_tokens.session_id",
                f"{SCHEMA}.auth_refresh_tokens.id",
            ],
            name="fk_auth_refresh_replacement_same_session",
            ondelete="SET NULL (replaced_by_token_id)",
        ),
        Index(
            "uq_auth_refresh_tokens_hash",
            "token_hash",
            unique=True,
        ),
        Index(
            "idx_auth_refresh_tokens_session_issued",
            "session_id",
            text("issued_at DESC"),
        ),
        Index(
            "uq_auth_refresh_one_active_per_session",
            "session_id",
            unique=True,
            postgresql_where=text(
                "consumed_at IS NULL AND revoked_at IS NULL"
            ),
        ),
        Index(
            "idx_auth_refresh_tokens_active_expiry",
            "expires_at",
            postgresql_where=text(
                "consumed_at IS NULL AND revoked_at IS NULL"
            ),
        ),
        Index(
            "uq_auth_refresh_replaced_by",
            "replaced_by_token_id",
            unique=True,
            postgresql_where=text(
                "replaced_by_token_id IS NOT NULL"
            ),
        ),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid_v4,
        server_default=text("gen_random_uuid()"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            f"{SCHEMA}.auth_sessions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    token_hash: Mapped[bytes] = mapped_column(
        BYTEA,
        nullable=False,
    )

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    revoke_reason: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    replaced_by_token_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    # Relaciones ORM

    session: Mapped[AuthSession] = relationship(
        back_populates="refresh_tokens",
    )

        # Token sucesor al que apunta este registro.
    replaced_by: Mapped[AuthRefreshToken | None] = relationship(
        back_populates="replaces",
        primaryjoin=lambda: (
            AuthRefreshToken.replaced_by_token_id
            == remote(AuthRefreshToken.id)
        ),
        foreign_keys=lambda: [
            AuthRefreshToken.replaced_by_token_id
        ],
        remote_side=lambda: [
            AuthRefreshToken.id
        ],
        uselist=False,
    )

    # Token anterior que apunta a este registro.
    replaces: Mapped[AuthRefreshToken | None] = relationship(
        back_populates="replaced_by",
        primaryjoin=lambda: (
            foreign(AuthRefreshToken.replaced_by_token_id)
            == AuthRefreshToken.id
        ),
        foreign_keys=lambda: [
            AuthRefreshToken.replaced_by_token_id
        ],
        uselist=False,
        viewonly=True,
    )


# ============================================================
# 4. PASSWORD_RECOVERY_TOKENS
# ============================================================

class PasswordRecoveryToken(Base):

    __tablename__ = "password_recovery_tokens"

    __table_args__ = (
        CheckConstraint(
            "octet_length(token_hash) = 32",
            name="ck_recovery_token_hash_length",
        ),
        CheckConstraint(
            """
            expires_at > issued_at
            AND expires_at <= issued_at + INTERVAL '30 minutes'
            """,
            name="ck_recovery_token_expiration",
        ),
        CheckConstraint(
            """
            NOT (
                consumed_at IS NOT NULL
                AND revoked_at IS NOT NULL
            )
            """,
            name="ck_recovery_token_state",
        ),
        CheckConstraint(
            """
            consumed_at IS NULL
            OR consumed_at >= issued_at
            """,
            name="ck_recovery_token_consumed_at",
        ),
        CheckConstraint(
            """
            revoked_at IS NULL
            OR revoked_at >= issued_at
            """,
            name="ck_recovery_token_revoked_at",
        ),
        Index(
            "uq_password_recovery_token_hash",
            "token_hash",
            unique=True,
        ),
        Index(
            "idx_password_recovery_user_issued",
            "user_id",
            text("issued_at DESC"),
        ),
        Index(
            "uq_password_recovery_one_active_per_user",
            "user_id",
            unique=True,
            postgresql_where=text(
                "consumed_at IS NULL AND revoked_at IS NULL"
            ),
        ),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid_v4,
        server_default=text("gen_random_uuid()"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            f"{SCHEMA}.users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    token_hash: Mapped[bytes] = mapped_column(
        BYTEA,
        nullable=False,
    )

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Valor calculado por la aplicación:
    # expires_at = issued_at + timedelta(minutes=30)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped[User] = relationship(
        back_populates="password_recovery_tokens",
    )


# ============================================================
# 5. EMAIL_VERIFICATION_TOKENS
# ============================================================

class EmailVerificationToken(Base):

    __tablename__ = "email_verification_tokens"

    __table_args__ = (
        CheckConstraint(
            "octet_length(token_hash) = 32",
            name="ck_email_verification_hash_length",
        ),
        CheckConstraint(
            "expires_at > issued_at",
            name="ck_email_verification_expiration",
        ),
        CheckConstraint(
            """
            NOT (
                consumed_at IS NOT NULL
                AND revoked_at IS NOT NULL
            )
            """,
            name="ck_email_verification_state",
        ),
        CheckConstraint(
            """
            consumed_at IS NULL
            OR consumed_at >= issued_at
            """,
            name="ck_email_verification_consumed_at",
        ),
        CheckConstraint(
            """
            revoked_at IS NULL
            OR revoked_at >= issued_at
            """,
            name="ck_email_verification_revoked_at",
        ),
        Index(
            "uq_email_verification_token_hash",
            "token_hash",
            unique=True,
        ),
        Index(
            "idx_email_verification_user_issued",
            "user_id",
            text("issued_at DESC"),
        ),
        Index(
            "uq_email_verification_one_active_per_user",
            "user_id",
            unique=True,
            postgresql_where=text(
                "consumed_at IS NULL AND revoked_at IS NULL"
            ),
        ),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid_v4,
        server_default=text("gen_random_uuid()"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            f"{SCHEMA}.users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    token_hash: Mapped[bytes] = mapped_column(
        BYTEA,
        nullable=False,
    )

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # La vigencia exacta se define mediante política de CU01.
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped[User] = relationship(
        back_populates="email_verification_tokens",
    )


# ============================================================
# 6. AUDIT_EVENTS
# ============================================================

class AuditEvent(Base):

    __tablename__ = "audit_events"

    __table_args__ = (
        CheckConstraint(
            """
            event_type IN (
                'account_registered',
                'email_verification_completed',
                'login_succeeded',
                'login_failed',
                'login_locked',
                'session_created',
                'logout',
                'session_revoked',
                'sessions_revoked_all',
                'refresh_rotated',
                'refresh_reuse_detected',
                'password_changed',
                'password_recovery_requested',
                'password_recovery_completed',
                'account_suspended',
                'account_disabled'
            )
            """,
            name="ck_audit_event_type",
        ),
        CheckConstraint(
            """
            outcome IN (
                'success',
                'failure',
                'blocked',
                'security_event'
            )
            """,
            name="ck_audit_outcome",
        ),
        CheckConstraint(
            "jsonb_typeof(metadata) = 'object'",
            name="ck_audit_metadata_object",
        ),
        Index(
            "idx_audit_events_user_time",
            "user_id",
            text("occurred_at DESC"),
            postgresql_where=text("user_id IS NOT NULL"),
        ),
        Index(
            "idx_audit_events_session_time",
            "session_id",
            text("occurred_at DESC"),
            postgresql_where=text("session_id IS NOT NULL"),
        ),
        Index(
            "idx_audit_events_type_time",
            "event_type",
            text("occurred_at DESC"),
        ),
        Index(
            "idx_audit_events_occurred_at",
            text("occurred_at DESC"),
        ),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid_v4,
        server_default=text("gen_random_uuid()"),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            f"{SCHEMA}.users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    session_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            f"{SCHEMA}.auth_sessions.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    outcome: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    ip_address: Mapped[str | None] = mapped_column(
        INET,
        nullable=True,
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    request_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    # "metadata" es un nombre reservado por DeclarativeBase.
    # En Python se utiliza event_metadata, pero la columna física
    # de PostgreSQL conserva el nombre "metadata".
    event_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    user: Mapped[User | None] = relationship(
        back_populates="audit_events",
    )

    session: Mapped[AuthSession | None] = relationship(
        back_populates="audit_events",
    )