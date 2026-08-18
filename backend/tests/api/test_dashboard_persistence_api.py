"""PostgreSQL-to-API integration verification for dashboard metrics."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text

from app import create_app
from app.application.consultation_service import ConsultationApplicationService
from app.application.dashboard_service import DashboardApplicationService
from app.infrastructure.consultation_models import (
    Appointment,
    Consultation,
    ConsultationRecommendation,
    ConsultationStatus,
    ConsultationSummary,
)
from app.infrastructure.database import create_database_engine, create_session_factory
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.dashboard_repository import DashboardRepository

BACKEND_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def persisted_dashboard(postgresql_url: str):
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", postgresql_url)
    command.upgrade(config, "head")

    engine = create_database_engine(postgresql_url)
    session_factory = create_session_factory(engine)
    with session_factory.begin() as cleanup_session:
        cleanup_session.execute(text("DELETE FROM appointments"))
        cleanup_session.execute(text("DELETE FROM consultation_recommendations"))
        cleanup_session.execute(text("DELETE FROM consultation_summaries"))
        cleanup_session.execute(text("DELETE FROM messages"))
        cleanup_session.execute(text("DELETE FROM consultations"))

    session = session_factory()
    service = DashboardApplicationService(DashboardRepository(session))
    application = create_app(dashboard_service=service)
    application.config.update(TESTING=True)
    try:
        yield application.test_client(), session, session_factory
    finally:
        session.rollback()
        session.execute(text("DELETE FROM appointments"))
        session.execute(text("DELETE FROM consultation_recommendations"))
        session.execute(text("DELETE FROM consultation_summaries"))
        session.execute(text("DELETE FROM messages"))
        session.execute(text("DELETE FROM consultations"))
        session.commit()
        session.close()
        engine.dispose()


def test_empty_database_flows_through_repository_service_and_api(
    persisted_dashboard,
) -> None:
    client, _session, _session_factory = persisted_dashboard

    response = client.get("/api/v1/dashboard")

    assert response.status_code == 200
    assert response.get_json() == {
        "total_consultations": 0,
        "booked_appointments": 0,
        "conversion_rate": 0.0,
    }


def test_mixed_persisted_state_uses_appointment_rows_as_numerator(
    persisted_dashboard,
) -> None:
    client, session, _session_factory = persisted_dashboard
    pending = _consultation(ConsultationStatus.PENDING, "Pending")
    completed = _consultation(ConsultationStatus.COMPLETED, "Completed")
    booked_status_only = _consultation(ConsultationStatus.BOOKED, "Status only")
    session.add_all([pending, completed, booked_status_only])
    session.flush()

    summary = ConsultationSummary(
        id=uuid4(),
        consultation_id=completed.id,
        patient_summary="Persisted summary",
        recommendation_rationale=None,
    )
    session.add(summary)
    session.flush()
    recommendation = ConsultationRecommendation(
        id=uuid4(),
        summary_id=summary.id,
        treatment="Physical therapy",
        position=1,
    )
    session.add(recommendation)
    session.flush()
    session.add(
        Appointment(
            id=uuid4(),
            consultation_id=completed.id,
            recommendation_id=recommendation.id,
            scheduled_at=datetime(2026, 8, 20, 14, 30, tzinfo=timezone.utc),
            location="Downtown Clinic",
        )
    )
    session.commit()

    response = client.get("/api/v1/dashboard")

    assert response.status_code == 200
    assert response.get_json() == {
        "total_consultations": 3,
        "booked_appointments": 1,
        "conversion_rate": 33.33,
    }


def test_feature_004_booking_updates_fresh_dashboard_read_exactly_once(
    persisted_dashboard,
) -> None:
    client, session, session_factory = persisted_dashboard
    pending = _consultation(ConsultationStatus.PENDING, "Pending")
    completed = _consultation(ConsultationStatus.COMPLETED, "Eligible")
    booked_status_only = _consultation(ConsultationStatus.BOOKED, "Status only")
    session.add_all([pending, completed, booked_status_only])
    session.flush()
    summary = ConsultationSummary(
        id=uuid4(),
        consultation_id=completed.id,
        patient_summary="Persisted summary",
        recommendation_rationale="Persisted rationale",
    )
    session.add(summary)
    session.flush()
    recommendation = ConsultationRecommendation(
        id=uuid4(),
        summary_id=summary.id,
        treatment="Physical therapy",
        position=1,
    )
    session.add(recommendation)
    session.commit()

    assert client.get("/api/v1/dashboard").get_json() == {
        "total_consultations": 3,
        "booked_appointments": 0,
        "conversion_rate": 0.0,
    }

    client.application.extensions["consultation_service"] = (
        ConsultationApplicationService(
            ConsultationRepository(session),
            appointment_repository=AppointmentRepository(session),
            clock=lambda: datetime(2026, 8, 18, 12, 0, tzinfo=timezone.utc),
        )
    )
    booking_body = {
        "recommendation_id": str(recommendation.id),
        "scheduled_at": "2026-08-20T14:30:00Z",
        "location": "Downtown Clinic",
    }
    booking = client.post(
        f"/api/v1/consultations/{completed.id}/appointments", json=booking_body
    )
    assert booking.status_code == 201

    with session_factory() as fresh_session:
        client.application.extensions["dashboard_service"] = (
            DashboardApplicationService(DashboardRepository(fresh_session))
        )
        refreshed = client.get("/api/v1/dashboard")
        assert refreshed.status_code == 200
        assert refreshed.get_json() == {
            "total_consultations": 3,
            "booked_appointments": 1,
            "conversion_rate": 33.33,
        }
        assert fresh_session.get(Consultation, completed.id).status is ConsultationStatus.BOOKED
        assert fresh_session.query(Appointment).count() == 1

    duplicate = client.post(
        f"/api/v1/consultations/{completed.id}/appointments", json=booking_body
    )
    assert duplicate.status_code == 409
    session.expire_all()
    assert session.query(Appointment).count() == 1


def _consultation(status: ConsultationStatus, patient_name: str) -> Consultation:
    return Consultation(
        id=uuid4(),
        patient_name=patient_name,
        primary_concern="Persistent knee pain",
        recommended_procedure="Physical therapy",
        status=status,
    )
