"""Repository coordination for atomic consultation appointment booking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.infrastructure.consultation_models import (
    Appointment,
    Consultation,
    ConsultationRecommendation,
    ConsultationStatus,
    ConsultationSummary,
)


APPOINTMENT_CONSULTATION_UNIQUE_CONSTRAINT = "uq_appointments_consultation_id"


@dataclass(frozen=True)
class AppointmentAggregate:
    """A persisted appointment and its authoritative recommendation."""

    appointment: Appointment
    recommendation: ConsultationRecommendation


@dataclass(frozen=True)
class AppointmentCreation:
    """Result of an atomic create or exact duplicate-winner reconciliation."""

    aggregate: AppointmentAggregate
    created: bool


@dataclass(frozen=True)
class AppointmentListItem:
    """Authoritative appointment list projection across persisted lineage."""

    id: UUID
    consultation_id: UUID
    patient_name: str
    recommendation_id: UUID
    treatment: str
    scheduled_at: datetime
    location: str
    created_at: datetime


class AppointmentRepository:
    """Own booking-specific reads, locking, and transaction mechanics."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def lock_consultation(self, consultation_id: UUID) -> Consultation | None:
        """Load and lock the consultation row for booking coordination."""
        return self._session.scalar(
            select(Consultation)
            .where(Consultation.id == consultation_id)
            .with_for_update()
        )

    def get_appointment(self, consultation_id: UUID) -> Appointment | None:
        """Return the consultation's appointment, when one exists."""
        return self._session.scalar(
            select(Appointment).where(Appointment.consultation_id == consultation_id)
        )

    def get_summary(self, consultation_id: UUID) -> ConsultationSummary | None:
        """Return the consultation's persisted summary parent."""
        return self._session.scalar(
            select(ConsultationSummary).where(
                ConsultationSummary.consultation_id == consultation_id
            )
        )

    def get_recommendation(
        self, recommendation_id: UUID
    ) -> ConsultationRecommendation | None:
        """Resolve a recommendation globally so missing and mismatched differ."""
        return self._session.get(ConsultationRecommendation, recommendation_id)

    def get_owned_recommendation(
        self, consultation_id: UUID, recommendation_id: UUID
    ) -> ConsultationRecommendation | None:
        """Return the recommendation only through this consultation's lineage."""
        return self._session.scalar(
            select(ConsultationRecommendation)
            .join(
                ConsultationSummary,
                ConsultationRecommendation.summary_id == ConsultationSummary.id,
            )
            .where(
                ConsultationRecommendation.id == recommendation_id,
                ConsultationSummary.consultation_id == consultation_id,
            )
        )

    def list_appointments(self) -> list[AppointmentListItem]:
        """Return one ordered projection for every persisted appointment."""
        rows = self._session.execute(
            select(
                Appointment.id,
                Appointment.consultation_id,
                Consultation.patient_name,
                ConsultationRecommendation.id,
                ConsultationRecommendation.treatment,
                Appointment.scheduled_at,
                Appointment.location,
                Appointment.created_at,
            )
            .join(
                Consultation,
                Appointment.consultation_id == Consultation.id,
            )
            .join(
                ConsultationRecommendation,
                Appointment.recommendation_id == ConsultationRecommendation.id,
            )
            .join(
                ConsultationSummary,
                and_(
                    ConsultationRecommendation.summary_id
                    == ConsultationSummary.id,
                    ConsultationSummary.consultation_id == Appointment.consultation_id,
                ),
            )
            .order_by(Appointment.scheduled_at.asc(), Appointment.id.asc())
        ).all()
        return [
            AppointmentListItem(
                id=row[0],
                consultation_id=row[1],
                patient_name=row[2],
                recommendation_id=row[3],
                treatment=row[4],
                scheduled_at=row[5],
                location=row[6],
                created_at=row[7],
            )
            for row in rows
        ]

    def abort(self) -> None:
        """Roll back a non-successful coordinated booking and release its lock."""
        self._session.rollback()

    def create_appointment(
        self,
        consultation: Consultation,
        recommendation: ConsultationRecommendation,
        *,
        scheduled_at: datetime,
        location: str,
    ) -> AppointmentCreation:
        """Insert an appointment and mark its consultation BOOKED in one commit."""
        appointment = Appointment(
            consultation_id=consultation.id,
            recommendation_id=recommendation.id,
            scheduled_at=scheduled_at,
            location=location,
        )

        try:
            self._session.add(appointment)
            self._session.flush()
            consultation.status = ConsultationStatus.BOOKED
            self._session.commit()
            aggregate = self._reload_aggregate(appointment.id)
            if aggregate is None:  # pragma: no cover - defensive post-commit guard
                raise RuntimeError("committed appointment could not be reloaded")
            return AppointmentCreation(aggregate=aggregate, created=True)
        except IntegrityError as error:
            self._session.rollback()
            if self._constraint_name(error) != (
                APPOINTMENT_CONSULTATION_UNIQUE_CONSTRAINT
            ):
                raise

            winner = self.get_appointment(consultation.id)
            if winner is None:
                raise
            aggregate = self._reload_aggregate(winner.id)
            if aggregate is None:
                raise
            return AppointmentCreation(aggregate=aggregate, created=False)
        except Exception:
            # This cannot undo a transaction whose commit succeeded; it does keep
            # every pre-commit failure atomic and restores a failed shared session.
            self._session.rollback()
            raise

    def _reload_aggregate(self, appointment_id: UUID) -> AppointmentAggregate | None:
        row = self._session.execute(
            select(Appointment, ConsultationRecommendation)
            .join(
                ConsultationRecommendation,
                Appointment.recommendation_id == ConsultationRecommendation.id,
            )
            .where(Appointment.id == appointment_id)
        ).one_or_none()
        if row is None:
            return None
        return AppointmentAggregate(appointment=row[0], recommendation=row[1])

    @staticmethod
    def _constraint_name(error: IntegrityError) -> str | None:
        diagnostic = getattr(error.orig, "diag", None)
        return getattr(diagnostic, "constraint_name", None)
