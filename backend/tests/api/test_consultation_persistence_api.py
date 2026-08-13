"""PostgreSQL-to-API integration verification for Consultation Records."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config

from app import create_app
from app.application.consultation_service import ConsultationApplicationService
from app.infrastructure.consultation_models import Consultation, ConsultationStatus
from app.infrastructure.database import create_database_engine, create_session_factory
from app.repositories.consultation_repository import ConsultationRepository


BACKEND_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def persisted_client(postgresql_url: str):
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", postgresql_url)
    command.upgrade(config, "head")

    engine = create_database_engine(postgresql_url)
    session_factory = create_session_factory(engine)
    session = session_factory()
    records = [
        Consultation(
            patient_name="Amina Khan",
            primary_concern="Persistent knee pain",
            recommended_procedure="Physical therapy",
            status=ConsultationStatus.PENDING,
        ),
        Consultation(
            patient_name="Bilal Ahmed",
            primary_concern="Migraine review",
            recommended_procedure="Neurology consultation",
            status=ConsultationStatus.BOOKED,
        ),
        Consultation(
            patient_name="Carla Diaz",
            primary_concern="Shoulder stiffness",
            recommended_procedure="Mobility program",
            status=ConsultationStatus.COMPLETED,
        ),
    ]
    session.add_all(records)
    session.commit()

    app = create_app(
        ConsultationApplicationService(ConsultationRepository(session))
    )
    app.config.update(TESTING=True)
    yield app.test_client(), records

    session.close()
    engine.dispose()


def test_persisted_records_flow_through_repository_service_and_api(
    persisted_client,
) -> None:
    client, records = persisted_client

    response = client.get("/api/v1/consultations")
    assert response.status_code == 200
    assert {item["id"] for item in response.get_json()["items"]} == {
        str(record.id) for record in records
    }

    search_response = client.get("/api/v1/consultations?search=NEUROLOGY")
    assert [item["patient_name"] for item in search_response.get_json()["items"]] == [
        "Bilal Ahmed"
    ]

    for status in ConsultationStatus:
        status_response = client.get(f"/api/v1/consultations?status={status.value}")
        assert status_response.status_code == 200
        assert [item["status"] for item in status_response.get_json()["items"]] == [
            status.value
        ]

    combined_response = client.get(
        "/api/v1/consultations?search=knee&status=PENDING"
    )
    assert [item["patient_name"] for item in combined_response.get_json()["items"]] == [
        "Amina Khan"
    ]

    detail_response = client.get(f"/api/v1/consultations/{records[0].id}")
    assert detail_response.status_code == 200
    assert detail_response.get_json()["id"] == str(records[0].id)

    missing_response = client.get(f"/api/v1/consultations/{uuid4()}")
    assert missing_response.status_code == 404
    assert missing_response.get_json() == {"error": "Consultation not found"}
