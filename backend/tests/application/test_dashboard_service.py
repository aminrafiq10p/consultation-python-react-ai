"""DN-003 deterministic dashboard application workflow coverage."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.application.dashboard_service import (
    DashboardApplicationService,
    DashboardMetrics,
    InvalidDashboardCountsError,
)
from app.repositories.dashboard_repository import DashboardCounts


class CountOnlyRepository:
    """Strict double exposing only the dashboard aggregate operation."""

    __slots__ = ("calls", "counts", "failure")

    def __init__(
        self,
        counts: DashboardCounts,
        *,
        failure: Exception | None = None,
    ) -> None:
        self.counts = counts
        self.failure = failure
        self.calls = 0

    def get_counts(self) -> DashboardCounts:
        self.calls += 1
        if self.failure is not None:
            raise self.failure
        return self.counts


@pytest.mark.parametrize(
    ("total", "booked", "expected"),
    [
        (0, 0, "0.00"),
        (8, 0, "0.00"),
        (1, 1, "100.00"),
        (2, 1, "50.00"),
        (4, 1, "25.00"),
        (3, 1, "33.33"),
        (3, 2, "66.67"),
        (32, 1, "3.13"),
        (100_000, 72_345, "72.35"),
    ],
)
def test_metrics_use_exact_two_decimal_half_up_calculation(
    total: int, booked: int, expected: str
) -> None:
    repository = CountOnlyRepository(DashboardCounts(total, booked))

    result = DashboardApplicationService(repository).get_metrics()

    assert result == DashboardMetrics(total, booked, Decimal(expected))
    assert isinstance(result.total_consultations, int)
    assert isinstance(result.booked_appointments, int)
    assert isinstance(result.conversion_rate, Decimal)
    assert result.conversion_rate.as_tuple().exponent == -2
    assert repository.calls == 1


@pytest.mark.parametrize(
    ("total", "booked"),
    [
        (-1, 0),
        (1, -1),
        (1.0, 0),
        (1, 0.0),
        (True, 0),
        (1, False),
    ],
)
def test_invalid_repository_counts_are_rejected_after_one_read(
    total: object, booked: object
) -> None:
    repository = CountOnlyRepository(DashboardCounts(total, booked))  # type: ignore[arg-type]

    with pytest.raises(InvalidDashboardCountsError):
        DashboardApplicationService(repository).get_metrics()

    assert repository.calls == 1


def test_count_above_total_is_not_repaired_by_application_service() -> None:
    repository = CountOnlyRepository(DashboardCounts(1, 2))

    result = DashboardApplicationService(repository).get_metrics()

    assert result == DashboardMetrics(1, 2, Decimal("200.00"))
    assert repository.calls == 1


def test_repository_failure_propagates_unchanged_after_one_read() -> None:
    failure = OSError("persistence unavailable")
    repository = CountOnlyRepository(DashboardCounts(0, 0), failure=failure)

    with pytest.raises(OSError) as raised:
        DashboardApplicationService(repository).get_metrics()

    assert raised.value is failure
    assert repository.calls == 1


def test_metrics_read_does_not_mutate_repository_value() -> None:
    counts = DashboardCounts(7, 3)
    repository = CountOnlyRepository(counts)

    DashboardApplicationService(repository).get_metrics()

    assert repository.counts is counts
    assert repository.counts == DashboardCounts(7, 3)
    assert repository.calls == 1
