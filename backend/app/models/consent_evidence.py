from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Identity, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ConsentEvidence(Base):
    __tablename__ = "consent_evidence"
    __table_args__ = (
        CheckConstraint("document_kind IN ('terms', 'privacy', 'health_data')", name="evidence_kind"),
        CheckConstraint("document_status IN ('test', 'draft', 'approved')", name="evidence_status"),
        CheckConstraint("document_sha256 ~ '^[a-f0-9]{64}$'", name="evidence_checksum"),
        CheckConstraint("document_kind = 'health_data' OR accepted", name="evidence_decision"),
        {"schema": "glucovida"},
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("glucovida.users.id", ondelete="CASCADE"), index=True
    )
    document_kind: Mapped[str] = mapped_column(String(16))
    document_version: Mapped[str] = mapped_column(String(64))
    document_status: Mapped[str] = mapped_column(String(8))
    document_sha256: Mapped[str] = mapped_column(String(64))
    accepted: Mapped[bool] = mapped_column(Boolean)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
