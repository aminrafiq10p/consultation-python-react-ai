"""Application services for consultation records."""

from __future__ import annotations

from uuid import UUID

from app.infrastructure.consultation_models import (
    Consultation,
    ConsultationStatus,
)
from app.repositories.consultation_repository import ConsultationRepository


class ConsultationNotFoundError(Exception):
    """Raised when a requested consultation does not exist."""


class ConsultationApplicationService:
    """Coordinates consultation-record use cases."""

    def __init__(
        self,
        repository: ConsultationRepository,
    ) -> None:
        self._repository = repository

    def list_consultations(
        self,
        *,
        search: str | None = None,
        status: ConsultationStatus | None = None,
    ) -> list[Consultation]:
        """Return consultation records using the validated filters unchanged."""
        return self._repository.get_consultations(
            search=search,
            status=status,
        )

    def get_consultation(
        self,
        consultation_id: UUID,
    ) -> Consultation:
        """Return one consultation or raise the application not-found outcome."""
        consultation = self._repository.get_consultation_by_id(
            consultation_id,
        )

        if consultation is None:
            raise ConsultationNotFoundError

        return consultation
