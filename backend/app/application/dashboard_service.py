"""Provider-neutral application workflow for dashboard metrics."""

from __future__ import annotations

from datetime import date, datetime
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Protocol, cast
from uuid import UUID

from app.infrastructure.consultation_models import ConsultationStatus

PERCENTAGE_QUANTUM = Decimal("0.01")
ONE_HUNDRED = Decimal(100)


class DashboardCountValues(Protocol):
    """Structural count value returned by the persistence boundary."""

    total_consultations: int
    booked_appointments: int


class DashboardCountsRepository(Protocol):
    """Narrow count-only dependency required by the dashboard workflow."""

    def get_counts(self) -> DashboardCountValues:
        """Return authoritative consultation and appointment counts."""
        ...


class DashboardProjectionRepository(DashboardCountsRepository, Protocol):
    """Read boundary required for the complete dashboard projection."""

    def get_consultation_trends(self) -> list[object]:
        """Return the populated daily consultation trend buckets."""
        ...

    def get_recent_activity(self) -> list[object]:
        """Return the bounded recent activity projection."""
        ...

    def get_pending_clinical_reviews(self) -> list[object]:
        """Return the bounded pending-consultation projection."""
        ...


class InvalidDashboardCountsError(ValueError):
    """Raised when a repository returns invalid dashboard counts."""


@dataclass(frozen=True)
class DashboardMetrics:
    """Validated dashboard counts and their exact conversion percentage."""

    total_consultations: int
    booked_appointments: int
    conversion_rate: Decimal


@dataclass(frozen=True)
class DashboardTrendProjection:
    """Application representation of one consultation trend bucket."""

    day: date
    consultation_count: int


@dataclass(frozen=True)
class DashboardActivityProjection:
    """Application representation of one recent activity item."""

    activity_type: str
    consultation_id: UUID
    timestamp: datetime


@dataclass(frozen=True)
class DashboardPendingClinicalReviewProjection:
    """Application representation of one pending consultation."""

    consultation_id: UUID
    patient_name: str
    primary_concern: str
    recommended_procedure: str
    status: ConsultationStatus


@dataclass(frozen=True)
class DashboardReadModel:
    """Complete read-only dashboard result returned by the application layer."""

    metrics: DashboardMetrics
    consultation_trends: tuple[DashboardTrendProjection, ...]
    recent_activity: tuple[DashboardActivityProjection, ...]
    pending_clinical_reviews: tuple[DashboardPendingClinicalReviewProjection, ...]


class DashboardApplicationService:
    """Calculate dashboard metrics from one authoritative aggregate read."""

    def __init__(self, repository: DashboardCountsRepository) -> None:
        self._repository = repository

    def get_metrics(self) -> DashboardMetrics:
        """Return validated counts and a two-decimal conversion percentage."""
        counts = self._repository.get_counts()
        self._validate_count(counts.total_consultations)
        self._validate_count(counts.booked_appointments)

        if counts.total_consultations == 0:
            conversion_rate = Decimal("0.00")
        else:
            conversion_rate = (
                Decimal(counts.booked_appointments)
                / Decimal(counts.total_consultations)
                * ONE_HUNDRED
            ).quantize(PERCENTAGE_QUANTUM, rounding=ROUND_HALF_UP)

        return DashboardMetrics(
            total_consultations=counts.total_consultations,
            booked_appointments=counts.booked_appointments,
            conversion_rate=conversion_rate,
        )

    def get_dashboard(self) -> DashboardReadModel:
        """Return metrics and all persisted dashboard read projections."""
        repository = cast(DashboardProjectionRepository, self._repository)

        trends = repository.get_consultation_trends()
        activity = repository.get_recent_activity()
        pending_reviews = repository.get_pending_clinical_reviews()
        return DashboardReadModel(
            metrics=self.get_metrics(),
            consultation_trends=tuple(
                DashboardTrendProjection(
                    day=item.day,
                    consultation_count=item.consultation_count,
                )
                for item in trends
            ),
            recent_activity=tuple(
                DashboardActivityProjection(
                    activity_type=item.activity_type,
                    consultation_id=item.consultation_id,
                    timestamp=item.timestamp,
                )
                for item in activity
            ),
            pending_clinical_reviews=tuple(
                DashboardPendingClinicalReviewProjection(
                    consultation_id=item.consultation_id,
                    patient_name=item.patient_name,
                    primary_concern=item.primary_concern,
                    recommended_procedure=item.recommended_procedure,
                    status=item.status,
                )
                for item in pending_reviews
            ),
        )

    @staticmethod
    def _validate_count(value: object) -> None:
        if type(value) is not int or value < 0:
            raise InvalidDashboardCountsError(
                "Dashboard counts must be nonnegative integers"
            )
