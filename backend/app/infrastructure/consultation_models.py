"""SQLAlchemy persistence mapping for consultation records."""

from __future__ import annotations

from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Enum as SqlAlchemyEnum
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative metadata owned by the infrastructure persistence layer."""


class ConsultationStatus(str, Enum):
    """The only consultation statuses approved for persisted records."""

    PENDING = "PENDING"
    BOOKED = "BOOKED"
    COMPLETED = "COMPLETED"


class Consultation(Base):
    """Persistence-only representation of a consultation record."""

    __tablename__ = "consultations"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    patient_name: Mapped[str] = mapped_column(Text, nullable=False)
    primary_concern: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_procedure: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ConsultationStatus] = mapped_column(
        SqlAlchemyEnum(
            ConsultationStatus,
            name="consultation_status",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )
