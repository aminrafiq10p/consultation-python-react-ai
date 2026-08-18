"""Provider-neutral application workflow for dashboard metrics."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Protocol

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


class InvalidDashboardCountsError(ValueError):
    """Raised when a repository returns invalid dashboard counts."""


@dataclass(frozen=True)
class DashboardMetrics:
    """Validated dashboard counts and their exact conversion percentage."""

    total_consultations: int
    booked_appointments: int
    conversion_rate: Decimal


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

    @staticmethod
    def _validate_count(value: object) -> None:
        if type(value) is not int or value < 0:
            raise InvalidDashboardCountsError(
                "Dashboard counts must be nonnegative integers"
            )
