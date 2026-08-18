"""HTTP-boundary coverage for deterministic appointment booking."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app import create_app
from app.application.consultation_service import (
    AppointmentAlreadyExistsError,
    ConsultationApplicationService,
    ConsultationNotBookableError,
    ConsultationNotFoundError,
    InvalidAppointmentBookingError,
    RecommendationNotBookableError,
    RecommendationNotFoundError,
)
from app.repositories.appointment_repository import AppointmentAggregate


@pytest.fixture
def service() -> Mock:
    return Mock(spec=ConsultationApplicationService)


@pytest.fixture
def client(service: Mock):
    app = create_app(service)
    app.config.update(TESTING=True)
    return app.test_client()


def valid_body(recommendation_id=None):
    return {
        "recommendation_id": str(recommendation_id or uuid4()),
        "scheduled_at": "2026-08-20T19:30:00+05:00",
        "location": "  Downtown Clinic  ",
    }


def aggregate(consultation_id, recommendation_id):
    return AppointmentAggregate(
        appointment=SimpleNamespace(
            id=uuid4(),
            consultation_id=consultation_id,
            recommendation_id=recommendation_id,
            scheduled_at=datetime(2026, 8, 20, 14, 30, tzinfo=UTC),
            location="Downtown Clinic",
            created_at=datetime(2026, 8, 18, 12, 0, tzinfo=UTC),
        ),
        recommendation=SimpleNamespace(
            id=recommendation_id, treatment="Physical therapy", summary_id=uuid4()
        ),
    )


def test_booking_delegates_once_and_returns_exact_201(client, service: Mock) -> None:
    consultation_id = uuid4()
    recommendation_id = uuid4()
    result = aggregate(consultation_id, recommendation_id)
    service.book_appointment.return_value = result

    response = client.post(
        f"/api/v1/consultations/{consultation_id}/appointments",
        json=valid_body(recommendation_id),
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body == {
        "id": str(result.appointment.id),
        "consultation_id": str(consultation_id),
        "recommendation": {
            "id": str(recommendation_id),
            "treatment": "Physical therapy",
        },
        "scheduled_at": "2026-08-20T14:30:00Z",
        "location": "Downtown Clinic",
        "created_at": "2026-08-18T12:00:00Z",
    }
    service.book_appointment.assert_called_once()
    args = service.book_appointment.call_args.args
    assert args[0] == consultation_id
    assert args[1] == recommendation_id
    assert args[2].utcoffset().total_seconds() == 18_000
    assert args[3] == "Downtown Clinic"
    assert "summary_id" not in response.get_data(as_text=True)


@pytest.mark.parametrize(
    ("path_id", "body", "raw"),
    [
        ("not-a-uuid", valid_body(), None),
        (str(uuid4()), None, None),
        (str(uuid4()), None, "{"),
        (str(uuid4()), {**valid_body(), "extra": True}, None),
        (str(uuid4()), {**valid_body(), "recommendation_id": "bad"}, None),
        (str(uuid4()), {**valid_body(), "scheduled_at": 123}, None),
        (str(uuid4()), {**valid_body(), "scheduled_at": "2026-02-30T10:00:00Z"}, None),
        (str(uuid4()), {**valid_body(), "scheduled_at": "2026-08-20"}, None),
        (str(uuid4()), {**valid_body(), "scheduled_at": "2026-08-20T14:30:00"}, None),
        (str(uuid4()), {**valid_body(), "location": "   "}, None),
        (str(uuid4()), {**valid_body(), "location": "x" * 201}, None),
    ],
)
def test_invalid_booking_requests_are_safe_and_do_not_delegate(
    client, service: Mock, path_id: str, body, raw: str | None
) -> None:
    if raw is not None:
        response = client.post(
            f"/api/v1/consultations/{path_id}/appointments",
            data=raw,
            content_type="application/json",
        )
    elif body is None:
        response = client.post(f"/api/v1/consultations/{path_id}/appointments")
    else:
        response = client.post(
            f"/api/v1/consultations/{path_id}/appointments", json=body
        )

    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid request"}
    service.book_appointment.assert_not_called()


@pytest.mark.parametrize(
    ("error", "status", "body"),
    [
        (ConsultationNotFoundError(), 404, {"error": "Consultation not found"}),
        (RecommendationNotFoundError(), 404, {"error": "Recommendation not found"}),
        (RecommendationNotBookableError(), 409, {"error": "Recommendation is not bookable", "code": "RECOMMENDATION_NOT_BOOKABLE"}),
        (ConsultationNotBookableError(), 409, {"error": "Consultation is not bookable", "code": "CONSULTATION_NOT_BOOKABLE"}),
        (AppointmentAlreadyExistsError(), 409, {"error": "Appointment already exists", "code": "APPOINTMENT_ALREADY_EXISTS"}),
        (InvalidAppointmentBookingError("internal validation detail"), 400, {"error": "Invalid request"}),
    ],
)
def test_booking_maps_typed_outcomes_exactly(client, service: Mock, error, status, body) -> None:
    service.book_appointment.side_effect = error
    response = client.post(
        f"/api/v1/consultations/{uuid4()}/appointments", json=valid_body()
    )
    assert response.status_code == status
    assert response.get_json() == body
    service.book_appointment.assert_called_once()


def test_unexpected_booking_failure_is_safe(client, service: Mock) -> None:
    secret = "uq_appointments_consultation_id SQL postgresql://user:secret@db"
    service.book_appointment.side_effect = RuntimeError(secret)

    response = client.post(
        f"/api/v1/consultations/{uuid4()}/appointments", json=valid_body()
    )

    assert response.status_code == 500
    assert response.get_json() == {"error": "Internal server error"}
    assert secret not in response.get_data(as_text=True)
