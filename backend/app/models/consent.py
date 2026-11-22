from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class RegistrationConsent(Base):
    __tablename__ = "registration_consents"
    __table_args__ = (
        CheckConstraint("terms_accepted", name="registration_terms_accepted"),
        CheckConstraint("btrim(terms_version) <> ''", name="registration_terms_version"),
        CheckConstraint("btrim(health_data_version) <> ''", name="registration_health_version"),
        {"schema": "glucovida"},
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("glucovida.users.id", ondelete="CASCADE"), primary_key=True
    )
    terms_accepted: Mapped[bool] = mapped_column(Boolean)
    terms_version: Mapped[str] = mapped_column(String(64))
    health_data_version: Mapped[str] = mapped_column(String(64))
    health_data_authorized: Mapped[bool] = mapped_column(Boolean)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
