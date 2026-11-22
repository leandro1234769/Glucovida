"""Preserve versioned, append-only consent evidence."""

import sqlalchemy as sa
from alembic import op

revision = "e91cb80d6a42"
down_revision = "9df1a43bb615"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "consent_evidence",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("document_kind", sa.String(16), nullable=False),
        sa.Column("document_version", sa.String(64), nullable=False),
        sa.Column("document_status", sa.String(8), nullable=False),
        sa.Column("document_sha256", sa.String(64), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "document_kind IN ('terms', 'privacy', 'health_data')", name=op.f("ck_evidence_kind")
        ),
        sa.CheckConstraint(
            "document_status IN ('test', 'draft', 'approved')", name=op.f("ck_evidence_status")
        ),
        sa.CheckConstraint("document_sha256 ~ '^[a-f0-9]{64}$'", name=op.f("ck_evidence_checksum")),
        sa.CheckConstraint("document_kind = 'health_data' OR accepted", name=op.f("ck_evidence_decision")),
        sa.ForeignKeyConstraint(
            ["user_id"], ["glucovida.users.id"], ondelete="CASCADE",
            name=op.f("fk_consent_evidence_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_consent_evidence")),
        schema="glucovida",
    )
    op.create_index(
        op.f("ix_glucovida_consent_evidence_user_id"), "consent_evidence", ["user_id"],
        schema="glucovida",
    )
    op.execute("""
        CREATE FUNCTION glucovida.protect_consent_evidence() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF TG_OP = 'DELETE' AND pg_trigger_depth() > 1 THEN
                RETURN OLD;
            END IF;
            RAISE EXCEPTION 'Consent evidence is append-only';
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER trg_protect_consent_evidence
        BEFORE UPDATE OR DELETE ON glucovida.consent_evidence
        FOR EACH ROW EXECUTE FUNCTION glucovida.protect_consent_evidence()
    """)


def downgrade() -> None:
    op.drop_table("consent_evidence", schema="glucovida")
    op.execute("DROP FUNCTION glucovida.protect_consent_evidence()")
