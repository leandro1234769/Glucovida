"""Store initial registration consent decisions."""

import sqlalchemy as sa
from alembic import op

revision = "9df1a43bb615"
down_revision = "44269e2f6f08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "registration_consents",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("terms_accepted", sa.Boolean(), nullable=False),
        sa.Column("terms_version", sa.String(64), nullable=False),
        sa.Column("health_data_version", sa.String(64), nullable=False),
        sa.Column("health_data_authorized", sa.Boolean(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("terms_accepted", name=op.f("ck_registration_terms_accepted")),
        sa.CheckConstraint("btrim(terms_version) <> ''", name=op.f("ck_registration_terms_version")),
        sa.CheckConstraint(
            "btrim(health_data_version) <> ''", name=op.f("ck_registration_health_version")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["glucovida.users.id"],
            name=op.f("fk_registration_consents_user_id_users"), ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_registration_consents")),
        schema="glucovida",
    )


def downgrade() -> None:
    op.drop_table("registration_consents", schema="glucovida")
