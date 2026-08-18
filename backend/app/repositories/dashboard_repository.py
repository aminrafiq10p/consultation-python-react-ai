"""Read-only repository for authoritative dashboard counts."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.consultation_models import Appointment, Consultation


@dataclass(frozen=True)
class DashboardCounts:
    """Persisted consultation and appointment row counts."""

    total_consultations: int
    booked_appointments: int


class DashboardRepository:
    """Provides the focused aggregate read used by the dashboard workflow."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_counts(self) -> DashboardCounts:
        """Count consultations and appointments independently in one statement."""
        total_consultations = select(func.count(Consultation.id)).scalar_subquery()
        booked_appointments = select(func.count(Appointment.id)).scalar_subquery()
        row = self._session.execute(
            select(
                total_consultations.label("total_consultations"),
                booked_appointments.label("booked_appointments"),
            )
        ).one()

        return DashboardCounts(
            total_consultations=int(row.total_consultations),
            booked_appointments=int(row.booked_appointments),
        )
