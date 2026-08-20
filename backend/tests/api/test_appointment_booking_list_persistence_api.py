"""AP-007 PostgreSQL continuity from Feature 004 booking to appointment list."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, select, text

import app as app_package
from app import create_app
from app.application.consultation_service import ConsultationApplicationService
from app.infrastructure.consultation_models import (
    Appointment,
    Consultation,
    ConsultationRecommendation,
    ConsultationStatus,
    ConsultationSummary,
)
from app.infrastructure.database import create_database_engine, create_session_factory


BACKEND_ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_SCHEDULED_AT = "2026-08-01T19:30:00+05:00"


@pytest.fixture
def persisted_application(postgresql_url: str, monkeypatch: pytest.MonkeyPatch):
    """Use production request composition against an isolated migrated database."""
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", postgresql_url)
    command.upgrade(config, "head")

    engine = create_database_engine(postgresql_url)
    session_factory = create_session_factory(engine)
    _clean(session_factory)
    strict_ai = Mock()
    strict_ai.generate_response.side_effect = AssertionError("booking/list called AI")
    strict_ai.generate_summary.side_effect = AssertionError("booking/list called AI")
    monkeypatch.setattr(
        app_package, "database_url_from_environment", lambda: postgresql_url
    )
    monkeypatch.setattr(app_package, "create_ai_service", lambda _environment: strict_ai)
    monkeypatch.setattr(
        app_package,
        "ConsultationApplicationService",
        lambda *args, **kwargs: ConsultationApplicationService(
            *args,
            **kwargs,
            clock=lambda: datetime(2026, 7, 31, 12, 0, tzinfo=UTC),
        ),
    )

    application = create_app()
    application.config.update(TESTING=True)
    try:
        yield application, session_factory, strict_ai
    finally:
        _clean(session_factory)
        engine.dispose()


def test_feature_004_booking_is_returned_by_feature_007_list_from_fresh_request(
    persisted_application,
) -> None:
    application, session_factory, strict_ai = persisted_application
    consultation, recommendation = _persist_completed_lineage(session_factory)
    client = application.test_client()

    with session_factory() as before_booking:
        assert before_booking.scalar(select(func.count()).select_from(Appointment)) == 0
    dashboard_before_booking = client.get("/api/v1/dashboard")
    assert dashboard_before_booking.status_code == 200
    assert dashboard_before_booking.get_json()["booked_appointments"] == 0

    booking = client.post(
        f"/api/v1/consultations/{consultation.id}/appointments",
        json={
            "recommendation_id": str(recommendation.id),
            "scheduled_at": HISTORICAL_SCHEDULED_AT,
            "location": "Downtown Clinic",
        },
    )

    assert booking.status_code == 201
    booking_body = booking.get_json()
    assert "consultation_session" not in application.extensions

    with session_factory() as fresh_after_booking:
        persisted = fresh_after_booking.scalar(
            select(Appointment).where(Appointment.id == UUID(booking_body["id"]))
        )
        assert persisted is not None
        assert fresh_after_booking.scalar(select(func.count()).select_from(Appointment)) == 1
        persisted_identity = (
            persisted.id,
            persisted.consultation_id,
            persisted.recommendation_id,
            persisted.scheduled_at,
            persisted.location,
            persisted.created_at,
        )
        persisted_status = fresh_after_booking.get(Consultation, consultation.id).status

    dashboard_after_booking = client.get("/api/v1/dashboard")
    assert dashboard_after_booking.status_code == 200
    assert dashboard_after_booking.get_json()["booked_appointments"] == 1

    listed = client.get("/api/v1/appointments")

    assert listed.status_code == 200
    assert "consultation_session" not in application.extensions
    assert listed.get_json() == {
        "items": [
            {
                "id": str(persisted_identity[0]),
                "consultation_id": str(persisted_identity[1]),
                "patient_name": "Amina Khan",
                "recommendation": {
                    "id": str(persisted_identity[2]),
                    "treatment": "Physical therapy",
                },
                "scheduled_at": "2026-08-01T14:30:00Z",
                "location": persisted_identity[4],
                "created_at": booking_body["created_at"],
            }
        ]
    }

    with session_factory() as fresh_after_list:
        reloaded = fresh_after_list.get(Appointment, persisted_identity[0])
        assert reloaded is not None
        assert (
            reloaded.id,
            reloaded.consultation_id,
            reloaded.recommendation_id,
            reloaded.scheduled_at,
            reloaded.location,
            reloaded.created_at,
        ) == persisted_identity
        assert fresh_after_list.get(Consultation, consultation.id).status is persisted_status
        assert fresh_after_list.scalar(select(func.count()).select_from(Appointment)) == 1

    dashboard_after_list = client.get("/api/v1/dashboard")
    assert dashboard_after_list.status_code == 200
    assert dashboard_after_list.get_json()["booked_appointments"] == 1

    assert persisted_identity[3] == datetime(2026, 8, 1, 14, 30, tzinfo=UTC)
    assert persisted_identity[5].isoformat().replace("+00:00", "Z") == booking_body[
        "created_at"
    ]
    assert persisted_status is ConsultationStatus.BOOKED
    strict_ai.generate_response.assert_not_called()
    strict_ai.generate_summary.assert_not_called()


def _persist_completed_lineage(session_factory):
    consultation = Consultation(
        id=uuid4(),
        patient_name="Amina Khan",
        primary_concern="Persistent knee pain",
        recommended_procedure="Compatibility projection only",
        status=ConsultationStatus.COMPLETED,
    )
    summary = ConsultationSummary(
        id=uuid4(),
        consultation_id=consultation.id,
        patient_summary="Persisted completed consultation",
        recommendation_rationale="Persisted rationale",
    )
    recommendation = ConsultationRecommendation(
        id=uuid4(),
        summary_id=summary.id,
        treatment="Physical therapy",
        position=1,
    )
    with session_factory.begin() as session:
        session.add(consultation)
        session.flush()
        session.add(summary)
        session.flush()
        session.add(recommendation)
    return consultation, recommendation


def _clean(session_factory) -> None:
    with session_factory.begin() as session:
        session.execute(text("DELETE FROM appointments"))
        session.execute(text("DELETE FROM consultation_recommendations"))
        session.execute(text("DELETE FROM consultation_summaries"))
        session.execute(text("DELETE FROM messages"))
        session.execute(text("DELETE FROM consultations"))
