"""SQLAlchemy persistence mapping for consultation records."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum as SqlAlchemyEnum
from sqlalchemy import ForeignKey, Index, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgreSQLUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative metadata owned by the infrastructure persistence layer."""


class ConsultationStatus(str, Enum):
    """The only consultation statuses approved for persisted records."""

    PENDING = "PENDING"
    BOOKED = "BOOKED"
    COMPLETED = "COMPLETED"


class MessageRole(str, Enum):
    """The approved participant roles for persisted consultation messages."""

    USER = "USER"
    ASSISTANT = "ASSISTANT"


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


class Message(Base):
    """Persistence-only representation of a consultation message."""

    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint(
            "role != 'USER' OR structured_payload IS NULL",
            name="ck_messages_user_structured_payload_null",
        ),
        Index(
            "ix_messages_consultation_id_created_at_id",
            "consultation_id",
            "created_at",
            "id",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    consultation_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("consultations.id"),
        nullable=False,
    )
    role: Mapped[MessageRole] = mapped_column(
        SqlAlchemyEnum(
            MessageRole,
            name="message_role",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured_payload: Mapped[dict[str, object] | list[object] | None] = mapped_column(
        JSONB(none_as_null=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )


class ConsultationSummary(Base):
    """Persistence-only representation of one consultation summary."""

    __tablename__ = "consultation_summaries"
    __table_args__ = (
        UniqueConstraint(
            "consultation_id",
            name="uq_consultation_summaries_consultation_id",
        ),
        CheckConstraint(
            "btrim(patient_summary) <> ''",
            name="ck_consultation_summaries_patient_summary_nonblank",
        ),
        CheckConstraint(
            "recommendation_rationale IS NULL "
            "OR btrim(recommendation_rationale) <> ''",
            name="ck_consultation_summaries_rationale_nonblank",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    consultation_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("consultations.id"),
        nullable=False,
    )
    patient_summary: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation_rationale: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )


class ConsultationRecommendation(Base):
    """Persistence-only representation of an ordered summary recommendation."""

    __tablename__ = "consultation_recommendations"
    __table_args__ = (
        CheckConstraint(
            "btrim(treatment) <> ''",
            name="ck_consultation_recommendations_treatment_nonblank",
        ),
        CheckConstraint(
            "position >= 1",
            name="ck_consultation_recommendations_position_positive",
        ),
        UniqueConstraint(
            "summary_id",
            "position",
            name="uq_consultation_recommendations_summary_position",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    summary_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("consultation_summaries.id"),
        nullable=False,
    )
    treatment: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
