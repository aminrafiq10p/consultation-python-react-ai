"""HTTP-boundary tests for dashboard metrics."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app import create_app
from app.application.dashboard_service import (
    DashboardApplicationService,
    DashboardActivityProjection,
    DashboardMetrics,
    DashboardPendingClinicalReviewProjection,
    DashboardReadModel,
    DashboardTrendProjection,
)
from app.infrastructure.consultation_models import ConsultationStatus


@pytest.fixture
def service() -> Mock:
    return Mock(spec=DashboardApplicationService)


@pytest.fixture
def client(service: Mock):
    app = create_app(dashboard_service=service)
    app.config.update(TESTING=True)
    return app.test_client()


def dashboard(metrics: DashboardMetrics) -> DashboardReadModel:
    return DashboardReadModel(metrics, (), (), ())


@pytest.mark.parametrize(
    ("metrics", "expected"),
    [
        (dashboard(DashboardMetrics(3, 1, Decimal("33.33"))), {
            "total_consultations": 3,
            "booked_appointments": 1,
            "conversion_rate": 33.33,
            "consultation_trends": [],
            "recent_activity": [],
            "pending_clinical_reviews": [],
        }),
        (dashboard(DashboardMetrics(0, 0, Decimal("0.00"))), {
            "total_consultations": 0,
            "booked_appointments": 0,
            "conversion_rate": 0.0,
            "consultation_trends": [],
            "recent_activity": [],
            "pending_clinical_reviews": [],
        }),
    ],
)
def test_success_returns_exact_numeric_contract(
    client, service: Mock, metrics: DashboardReadModel, expected: dict[str, object]
) -> None:
    service.get_dashboard.return_value = metrics

    response = client.get("/api/v1/dashboard")

    body = response.get_json()
    assert response.status_code == 200
    assert body == expected
    assert set(body) == {
        "total_consultations",
        "booked_appointments",
        "conversion_rate",
        "consultation_trends",
        "recent_activity",
        "pending_clinical_reviews",
    }
    assert type(body["total_consultations"]) is int
    assert type(body["booked_appointments"]) is int
    assert type(body["conversion_rate"]) is float
    service.get_dashboard.assert_called_once_with()


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
    service.get_dashboard.assert_not_called()


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
    service.get_dashboard.assert_not_called()


def test_unexpected_service_failure_returns_only_safe_500(
    client, service: Mock
) -> None:
    internal_detail = (
        "postgresql://user:secret@db SELECT appointments OPENAI_API_KEY=secret"
    )
    service.get_dashboard.side_effect = RuntimeError(internal_detail)

    response = client.get("/api/v1/dashboard")

    assert response.status_code == 500
    assert response.get_json() == {"error": "Internal server error"}
    assert internal_detail not in response.get_data(as_text=True)
    service.get_dashboard.assert_called_once_with()


@pytest.mark.parametrize(
    "metrics",
    [
        dashboard(DashboardMetrics(-1, 0, Decimal("0.00"))),
        dashboard(DashboardMetrics(1, 2, Decimal("200.00"))),
        dashboard(DashboardMetrics(1, 1, Decimal("NaN"))),
        dashboard(DashboardMetrics(True, 0, Decimal("0.00"))),
    ],
)
def test_invalid_application_output_maps_to_safe_500(
    client, service: Mock, metrics: DashboardMetrics
) -> None:
    service.get_dashboard.return_value = metrics

    response = client.get("/api/v1/dashboard")

    assert response.status_code == 500
    assert response.get_json() == {"error": "Internal server error"}
    service.get_dashboard.assert_called_once_with()


def test_populated_projections_have_deterministic_contract_shape(client, service: Mock) -> None:
    consultation_id = uuid4()
    service.get_dashboard.return_value = DashboardReadModel(
        metrics=DashboardMetrics(2, 1, Decimal("50.00")),
        consultation_trends=(DashboardTrendProjection(date(2026, 8, 20), 2),),
        recent_activity=(
            DashboardActivityProjection(
                "conversation_started",
                consultation_id,
                datetime(2026, 8, 20, 9, tzinfo=timezone.utc),
            ),
        ),
        pending_clinical_reviews=(
            DashboardPendingClinicalReviewProjection(
                consultation_id,
                "Ava Patient",
                "Knee pain",
                "Physical therapy",
                ConsultationStatus.PENDING,
            ),
        ),
    )

    response = client.get("/api/v1/dashboard")

    assert response.status_code == 200
    assert response.get_json() == {
        "total_consultations": 2,
        "booked_appointments": 1,
        "conversion_rate": 50.0,
        "consultation_trends": [{"day": "2026-08-20", "consultation_count": 2}],
        "recent_activity": [{
            "activity_type": "conversation_started",
            "consultation_id": str(consultation_id),
            "timestamp": "2026-08-20T09:00:00Z",
        }],
        "pending_clinical_reviews": [{
            "consultation_id": str(consultation_id),
            "patient_name": "Ava Patient",
            "primary_concern": "Knee pain",
            "recommended_procedure": "Physical therapy",
            "status": "PENDING",
        }],
    }
