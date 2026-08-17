"""Repository access for persisted consultation records."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.infrastructure.consultation_models import (
    Consultation,
    ConsultationStatus,
)


class ConsultationRepository:
    """Provides persistence operations for consultation records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_consultations(
        self,
        *,
        search: str | None = None,
        status: ConsultationStatus | None = None,
    ) -> list[Consultation]:
        """Retrieve consultations using the approved filters."""
        statement = select(Consultation)

        if search:
            search_pattern = f"%{search}%"
            statement = statement.where(
                or_(
                    Consultation.patient_name.ilike(search_pattern),
                    Consultation.primary_concern.ilike(search_pattern),
                    Consultation.recommended_procedure.ilike(search_pattern),
                )
            )

        if status is not None:
            statement = statement.where(
                Consultation.status == status
            )

        return list(self._session.scalars(statement).all())

    def get_consultation_by_id(
        self,
        consultation_id: UUID,
    ) -> Consultation | None:
        """Retrieve one consultation by identifier."""
        statement = select(Consultation).where(
            Consultation.id == consultation_id
        )

        return self._session.scalar(statement)

    def create_consultation(self, consultation: Consultation) -> Consultation:
        """Commit one new consultation for an application-approved restart."""
        try:
            self._session.add(consultation)
            self._session.commit()
            self._session.refresh(consultation)
        except Exception:
            self._session.rollback()
            raise

        return consultation
