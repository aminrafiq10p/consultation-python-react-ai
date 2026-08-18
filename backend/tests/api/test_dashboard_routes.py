"""HTTP-boundary tests for dashboard metrics."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import Mock

import pytest

from app import create_app
from app.application.dashboard_service import (
    DashboardApplicationService,
    DashboardMetrics,
)


@pytest.fixture
def service() -> Mock:
    return Mock(spec=DashboardApplicationService)


@pytest.fixture
def client(service: Mock):
    app = create_app(dashboard_service=service)
    app.config.update(TESTING=True)
    return app.test_client()


@pytest.mark.parametrize(
    ("metrics", "expected"),
    [
        (DashboardMetrics(3, 1, Decimal("33.33")), {
            "total_consultations": 3,
            "booked_appointments": 1,
            "conversion_rate": 33.33,
        }),
        (DashboardMetrics(0, 0, Decimal("0.00")), {
            "total_consultations": 0,
            "booked_appointments": 0,
            "conversion_rate": 0.0,
        }),
    ],
)
def test_success_returns_exact_numeric_contract(
    client, service: Mock, metrics: DashboardMetrics, expected: dict[str, object]
) -> None:
    service.get_metrics.return_value = metrics

    response = client.get("/api/v1/dashboard")

    body = response.get_json()
    assert response.status_code == 200
    assert body == expected
    assert set(body) == {
        "total_consultations",
        "booked_appointments",
        "conversion_rate",
    }
    assert type(body["total_consultations"]) is int
    assert type(body["booked_appointments"]) is int
    assert type(body["conversion_rate"]) is float
    service.get_metrics.assert_called_once_with()


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/dashboard?status=BOOKED",
        "/api/v1/dashboard?foo=bar",
        "/api/v1/dashboard?foo=bar&status=BOOKED",
    ],
)
def test_query_parameters_are_rejected_without_delegation(
    client, service: Mock, path: str
) -> None:
    response = client.get(path)

    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid request"}
    service.get_metrics.assert_not_called()


@pytest.mark.parametrize(
    ("data", "content_type"),
    [
        (b"{}", "application/json"),
        (b"null", "application/json"),
        (b"dashboard=true", "application/x-www-form-urlencoded"),
        (b"plain text", "text/plain"),
        (b"{malformed", "application/json"),
        (b" ", None),
    ],
)
def test_nonempty_bodies_are_rejected_without_delegation(
    client, service: Mock, data: bytes, content_type: str | None
) -> None:
    response = client.get(
        "/api/v1/dashboard", data=data, content_type=content_type
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid request"}
    service.get_metrics.assert_not_called()


def test_unexpected_service_failure_returns_only_safe_500(
    client, service: Mock
) -> None:
    internal_detail = (
        "postgresql://user:secret@db SELECT appointments OPENAI_API_KEY=secret"
    )
    service.get_metrics.side_effect = RuntimeError(internal_detail)

    response = client.get("/api/v1/dashboard")

    assert response.status_code == 500
    assert response.get_json() == {"error": "Internal server error"}
    assert internal_detail not in response.get_data(as_text=True)
    service.get_metrics.assert_called_once_with()


@pytest.mark.parametrize(
    "metrics",
    [
        DashboardMetrics(-1, 0, Decimal("0.00")),
        DashboardMetrics(1, 2, Decimal("200.00")),
        DashboardMetrics(1, 1, Decimal("NaN")),
        DashboardMetrics(True, 0, Decimal("0.00")),
    ],
)
def test_invalid_application_output_maps_to_safe_500(
    client, service: Mock, metrics: DashboardMetrics
) -> None:
    service.get_metrics.return_value = metrics

    response = client.get("/api/v1/dashboard")

    assert response.status_code == 500
    assert response.get_json() == {"error": "Internal server error"}
    service.get_metrics.assert_called_once_with()
