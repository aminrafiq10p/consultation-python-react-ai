"""HTTP-boundary coverage for the Feature 007 appointment-list contract."""

from datetime import UTC, datetime, timedelta, timezone
from unittest.mock import Mock, call
from uuid import uuid4

import pytest

from app import create_app
from app.application.consultation_service import ConsultationApplicationService
from app.repositories.appointment_repository import AppointmentListItem


@pytest.fixture
def service() -> Mock:
    return Mock(spec=ConsultationApplicationService)


@pytest.fixture
def client(service: Mock):
    app = create_app(service)
    app.config.update(TESTING=True)
    return app.test_client()


def appointment_list_item() -> AppointmentListItem:
    return AppointmentListItem(
        id=uuid4(),
        consultation_id=uuid4(),
        patient_name="Amina Khan",
        recommendation_id=uuid4(),
        treatment="Physical therapy",
        scheduled_at=datetime(2026, 8, 20, 19, 30, tzinfo=timezone(timedelta(hours=5))),
        location="Downtown Clinic",
        created_at=datetime(2026, 8, 18, 12, 0, tzinfo=UTC),
    )


def test_list_returns_exact_populated_envelope_and_delegates_once(
    client, service: Mock
) -> None:
    item = appointment_list_item()
    service.list_appointments.return_value = [item]

    response = client.get("/api/v1/appointments")

    assert response.status_code == 200
    assert response.get_json() == {
        "items": [
            {
                "id": str(item.id),
                "consultation_id": str(item.consultation_id),
                "patient_name": "Amina Khan",
                "recommendation": {
                    "id": str(item.recommendation_id),
                    "treatment": "Physical therapy",
                },
                "scheduled_at": "2026-08-20T19:30:00+05:00",
                "location": "Downtown Clinic",
                "created_at": "2026-08-18T12:00:00Z",
            }
        ]
    }
    assert service.mock_calls == [call.list_appointments()]


def test_list_returns_empty_envelope_for_no_persisted_appointments(
    client, service: Mock
) -> None:
    service.list_appointments.return_value = []

    response = client.get("/api/v1/appointments", content_type="application/json")

    assert response.status_code == 200
    assert response.get_json() == {"items": []}
    service.list_appointments.assert_called_once_with()


@pytest.mark.parametrize(
    ("path", "data", "content_type"),
    [
        ("/api/v1/appointments?unexpected=value", None, None),
        ("/api/v1/appointments?unexpected", None, None),
        ("/api/v1/appointments", b"{}", "application/json"),
        ("/api/v1/appointments", b"not a request body", "text/plain"),
    ],
)
def test_list_rejects_query_or_nonempty_body_before_service_invocation(
    client, service: Mock, path: str, data: bytes | None, content_type: str | None
) -> None:
    response = client.get(path, data=data, content_type=content_type)

    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid request"}
    service.list_appointments.assert_not_called()


def test_unexpected_list_failure_is_safe(client, service: Mock) -> None:
    secret = "postgresql://user:secret@db SELECT appointments"
    service.list_appointments.side_effect = RuntimeError(secret)

    response = client.get("/api/v1/appointments")

    assert response.status_code == 500
    assert response.get_json() == {"error": "Internal server error"}
    assert secret not in response.get_data(as_text=True)
    service.list_appointments.assert_called_once_with()
