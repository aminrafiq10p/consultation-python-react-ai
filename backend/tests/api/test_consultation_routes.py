"""HTTP-boundary tests for consultation record reads."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from app import create_app
from app.application.consultation_service import (
    ConsultationApplicationService,
    ConsultationNotFoundError,
)
from app.infrastructure.consultation_models import ConsultationStatus


def consultation(**overrides):
    values = {
        "id": uuid4(),
        "patient_name": "Amina Khan",
        "primary_concern": "Knee pain",
        "recommended_procedure": "Physical therapy",
        "status": ConsultationStatus.PENDING,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.fixture
def service() -> Mock:
    return Mock(spec=ConsultationApplicationService)


@pytest.fixture
def client(service: Mock):
    app = create_app(service)
    app.config.update(TESTING=True)
    return app.test_client()


def test_list_success_has_approved_five_field_shape(client, service: Mock) -> None:
    record = consultation()
    service.list_consultations.return_value = [record]

    response = client.get("/api/v1/consultations")

    assert response.status_code == 200
    assert response.get_json() == {
        "items": [
            {
                "id": str(record.id),
                "patient_name": "Amina Khan",
                "primary_concern": "Knee pain",
                "recommended_procedure": "Physical therapy",
                "status": "PENDING",
            }
        ]
    }
    service.list_consultations.assert_called_once_with(search=None, status=None)


def test_empty_list_is_successful(client, service: Mock) -> None:
    service.list_consultations.return_value = []

    response = client.get("/api/v1/consultations")

    assert response.status_code == 200
    assert response.get_json() == {"items": []}


@pytest.mark.parametrize(
    ("query", "search", "status"),
    [
        ("search=%20%20knee%20%20", "  knee  ", None),
        ("status=BOOKED", None, ConsultationStatus.BOOKED),
        (
            "search=therapy&status=COMPLETED",
            "therapy",
            ConsultationStatus.COMPLETED,
        ),
    ],
)
def test_valid_filters_are_forwarded_unchanged(
    client, service: Mock, query: str, search: str | None, status
) -> None:
    service.list_consultations.return_value = []

    response = client.get(f"/api/v1/consultations?{query}")

    assert response.status_code == 200
    service.list_consultations.assert_called_once_with(search=search, status=status)


@pytest.mark.parametrize("query", ["search=", "search=%20%20%20", "status=UNKNOWN"])
def test_invalid_list_input_returns_400(client, service: Mock, query: str) -> None:
    response = client.get(f"/api/v1/consultations?{query}")

    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid request"}
    service.list_consultations.assert_not_called()


def test_detail_success(client, service: Mock) -> None:
    record = consultation(status=ConsultationStatus.BOOKED)
    service.get_consultation.return_value = record

    response = client.get(f"/api/v1/consultations/{record.id}")

    assert response.status_code == 200
    assert set(response.get_json()) == {
        "id",
        "patient_name",
        "primary_concern",
        "recommended_procedure",
        "status",
    }
    service.get_consultation.assert_called_once_with(record.id)


def test_invalid_detail_uuid_returns_400(client, service: Mock) -> None:
    response = client.get("/api/v1/consultations/not-a-uuid")

    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid request"}
    service.get_consultation.assert_not_called()


def test_missing_detail_returns_404(client, service: Mock) -> None:
    consultation_id = uuid4()
    service.get_consultation.side_effect = ConsultationNotFoundError

    response = client.get(f"/api/v1/consultations/{consultation_id}")

    assert response.status_code == 404
    assert response.get_json() == {"error": "Consultation not found"}


@pytest.mark.parametrize("endpoint", ["list", "detail"])
def test_unexpected_service_failure_returns_safe_500(
    client, service: Mock, endpoint: str
) -> None:
    internal_detail = "postgresql://user:secret@db SQL SELECT consultations"
    if endpoint == "list":
        service.list_consultations.side_effect = RuntimeError(internal_detail)
        path = "/api/v1/consultations"
    else:
        service.get_consultation.side_effect = RuntimeError(internal_detail)
        path = f"/api/v1/consultations/{uuid4()}"

    response = client.get(path)

    assert response.status_code == 500
    assert response.get_json() == {"error": "Internal server error"}
    assert internal_detail not in response.get_data(as_text=True)
