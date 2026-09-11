"""PostgreSQL-to-API integration verification for Consultation Records."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, select

import app as app_package
from app import create_app
from app.ai import AIResult, AIService, create_ai_service
from app.application.consultation_service import ConsultationApplicationService
from app.infrastructure.consultation_models import (
    Appointment,
    Consultation,
    ConsultationRecommendation,
    ConsultationStatus,
    ConsultationSummary,
    Message,
)
from app.infrastructure.database import create_database_engine, create_session_factory
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.summary_repository import SummaryRepository


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

    service = ConsultationApplicationService(
        ConsultationRepository(session),
        MessageRepository(session),
        create_ai_service({"AI_PROVIDER": "mock"}),
        SummaryRepository(session),
        AppointmentRepository(session),
        clock=lambda: datetime(2026, 8, 18, 12, 0, tzinfo=UTC),
    )
    app = create_app(service)
    app.config.update(TESTING=True)
    try:
        yield app.test_client(), records, session, service
    finally:
        session.rollback()
        session.query(Appointment).delete()
        session.query(ConsultationRecommendation).delete()
        session.query(ConsultationSummary).delete()
        session.query(Message).delete()
        session.query(Consultation).delete()
        session.commit()
        session.close()
        engine.dispose()


def test_persisted_records_flow_through_repository_service_and_api(
    persisted_client,
) -> None:
    client, records, _session, _service = persisted_client

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


def test_create_consultation_uses_production_request_composition_and_reloads(
    postgresql_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """POST commits one pending row without invoking AI or child workflows."""
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", postgresql_url)
    command.upgrade(config, "head")

    engine = create_database_engine(postgresql_url)
    session_factory = create_session_factory(engine)
    strict_ai = Mock(spec=AIService)
    monkeypatch.setattr(
        app_package, "database_url_from_environment", lambda: postgresql_url
    )
    monkeypatch.setattr(app_package, "create_ai_service", lambda _environment: strict_ai)

    with session_factory.begin() as session:
        session.query(Appointment).delete()
        session.query(ConsultationRecommendation).delete()
        session.query(ConsultationSummary).delete()
        session.query(Message).delete()
        session.query(Consultation).delete()

    app = create_app()
    app.config.update(TESTING=True)
    try:
        with app.test_client() as client:
            created = client.post(
                "/api/v1/consultations",
                json={
                    "patient_name": "  Amina Khan  ",
                    "primary_concern": "  Persistent knee pain  ",
                },
            )
            assert created.status_code == 201
            body = created.get_json()
            assert set(body) == {
                "id",
                "patient_name",
                "primary_concern",
                "recommended_procedure",
                "status",
            }
            assert body["patient_name"] == "Amina Khan"
            assert body["primary_concern"] == "Persistent knee pain"
            assert body["recommended_procedure"] == ""
            assert body["status"] == "PENDING"

            detail = client.get(f"/api/v1/consultations/{body['id']}")
            listing = client.get("/api/v1/consultations")

        assert detail.status_code == 200
        assert detail.get_json() == body
        assert listing.status_code == 200
        assert [item["id"] for item in listing.get_json()["items"]] == [body["id"]]

        with session_factory() as fresh_session:
            persisted = fresh_session.get(Consultation, body["id"])
            assert persisted is not None
            assert str(persisted.id) == body["id"]
            assert persisted.patient_name == "Amina Khan"
            assert persisted.primary_concern == "Persistent knee pain"
            assert persisted.recommended_procedure == ""
            assert persisted.status is ConsultationStatus.PENDING
            assert fresh_session.scalar(select(func.count()).select_from(Consultation)) == 1
            assert fresh_session.scalar(select(func.count()).select_from(Message)) == 0
            assert fresh_session.scalar(select(func.count()).select_from(ConsultationSummary)) == 0
            assert (
                fresh_session.scalar(
                    select(func.count()).select_from(ConsultationRecommendation)
                )
                == 0
            )
            assert fresh_session.scalar(select(func.count()).select_from(Appointment)) == 0

        strict_ai.generate_response.assert_not_called()
        strict_ai.generate_summary.assert_not_called()
    finally:
        with session_factory.begin() as session:
            session.query(Appointment).delete()
            session.query(ConsultationRecommendation).delete()
            session.query(ConsultationSummary).delete()
            session.query(Message).delete()
            session.query(Consultation).delete()
        engine.dispose()


def test_new_consultation_lifecycle_is_authoritative_without_creation_side_effects(
    postgresql_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """NC-007: creation remains a single pending row until a user sends a message."""
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", postgresql_url)
    command.upgrade(config, "head")

    engine = create_database_engine(postgresql_url)
    session_factory = create_session_factory(engine)
    strict_ai = Mock(spec=AIService)
    strict_ai.generate_response.return_value = AIResult("Deterministic response")
    monkeypatch.setattr(
        app_package, "database_url_from_environment", lambda: postgresql_url
    )
    monkeypatch.setattr(app_package, "create_ai_service", lambda _environment: strict_ai)

    def row_counts() -> dict[str, int]:
        with session_factory() as session:
            return {
                "consultations": session.scalar(
                    select(func.count()).select_from(Consultation)
                ),
                "messages": session.scalar(select(func.count()).select_from(Message)),
                "summaries": session.scalar(
                    select(func.count()).select_from(ConsultationSummary)
                ),
                "recommendations": session.scalar(
                    select(func.count()).select_from(ConsultationRecommendation)
                ),
                "appointments": session.scalar(
                    select(func.count()).select_from(Appointment)
                ),
            }

    with session_factory.begin() as session:
        session.query(Appointment).delete()
        session.query(ConsultationRecommendation).delete()
        session.query(ConsultationSummary).delete()
        session.query(Message).delete()
        session.query(Consultation).delete()

    app = create_app()
    app.config.update(TESTING=True)
    try:
        with app.test_client() as client:
            before_dashboard = client.get("/api/v1/dashboard")
            assert before_dashboard.get_json() == {
                "total_consultations": 0,
                "booked_appointments": 0,
                "conversion_rate": 0.0,
                "consultation_trends": [],
                "recent_activity": [],
                "pending_clinical_reviews": [],
            }
            before_counts = row_counts()

            created = client.post(
                "/api/v1/consultations",
                json={
                    "patient_name": "  Amina Khan  ",
                    "primary_concern": "  Persistent knee pain  ",
                },
            )
            assert created.status_code == 201
            body = created.get_json()
            consultation_id = body["id"]
            assert body == {
                "id": consultation_id,
                "patient_name": "Amina Khan",
                "primary_concern": "Persistent knee pain",
                "recommended_procedure": "",
                "status": "PENDING",
            }

            detail = client.get(f"/api/v1/consultations/{consultation_id}")
            listing = client.get("/api/v1/consultations")
            empty_history = client.get(
                f"/api/v1/consultations/{consultation_id}/messages"
            )
            after_dashboard = client.get("/api/v1/dashboard")

            assert detail.status_code == 200
            assert detail.get_json() == body
            assert listing.status_code == 200
            assert listing.get_json() == {"items": [body]}
            assert empty_history.status_code == 200
            assert empty_history.get_json() == {"items": []}
            assert after_dashboard.get_json() == {
                "total_consultations": 1,
                "booked_appointments": 0,
                "conversion_rate": 0.0,
                "consultation_trends": [],
                "recent_activity": [],
                "pending_clinical_reviews": [{
                    "consultation_id": consultation_id,
                    "patient_name": "Amina Khan",
                    "primary_concern": "Persistent knee pain",
                    "recommended_procedure": "",
                    "status": "PENDING",
                }],
            }

            assert row_counts() == {
                "consultations": before_counts["consultations"] + 1,
                "messages": before_counts["messages"],
                "summaries": before_counts["summaries"],
                "recommendations": before_counts["recommendations"],
                "appointments": before_counts["appointments"],
            }
            strict_ai.generate_response.assert_not_called()
            strict_ai.generate_summary.assert_not_called()

            failed = client.post(
                "/api/v1/consultations",
                json={"patient_name": "   ", "primary_concern": "Still painful"},
            )
            assert failed.status_code == 400
            assert failed.get_json() == {"error": "Invalid request"}
            assert "id" not in failed.get_json()
            assert row_counts() == {
                "consultations": before_counts["consultations"] + 1,
                "messages": before_counts["messages"],
                "summaries": before_counts["summaries"],
                "recommendations": before_counts["recommendations"],
                "appointments": before_counts["appointments"],
            }
            assert client.get("/api/v1/dashboard").get_json() == after_dashboard.get_json()
            strict_ai.generate_response.assert_not_called()
            strict_ai.generate_summary.assert_not_called()

            first_exchange = client.post(
                f"/api/v1/consultations/{consultation_id}/messages",
                json={"content": "What can I do for the pain?"},
            )
            assert first_exchange.status_code == 200
            exchange = first_exchange.get_json()
            assert exchange["user_message"]["consultation_id"] == consultation_id
            assert exchange["assistant_message"]["consultation_id"] == consultation_id
            assert exchange["user_message"]["role"] == "USER"
            assert exchange["assistant_message"]["role"] == "ASSISTANT"
            assert exchange["assistant_message"]["content"] == "Deterministic response"

        strict_ai.generate_response.assert_called_once()
        strict_ai.generate_summary.assert_not_called()
        context, messages = strict_ai.generate_response.call_args.args
        assert context.consultation_id == consultation_id
        assert [(item.role, item.content) for item in messages] == [
            ("USER", "What can I do for the pain?")
        ]

        with session_factory() as fresh_session:
            persisted = fresh_session.get(Consultation, consultation_id)
            assert persisted is not None
            assert str(persisted.id) == consultation_id
            assert persisted.status is ConsultationStatus.PENDING
            assert persisted.recommended_procedure == ""
            messages = fresh_session.scalars(
                select(Message).where(Message.consultation_id == persisted.id)
            ).all()
            assert len(messages) == 2
            assert {str(item.consultation_id) for item in messages} == {consultation_id}
    finally:
        with session_factory.begin() as session:
            session.query(Appointment).delete()
            session.query(ConsultationRecommendation).delete()
            session.query(ConsultationSummary).delete()
            session.query(Message).delete()
            session.query(Consultation).delete()
        engine.dispose()


def test_repeated_messages_persist_and_reload_through_full_api_slice(
    persisted_client,
) -> None:
    client, records, _session, _service = persisted_client
    consultation_id = records[0].id

    first = client.post(
        f"/api/v1/consultations/{consultation_id}/messages",
        json={"content": "  First question  "},
    )
    second = client.post(
        f"/api/v1/consultations/{consultation_id}/messages",
        json={"content": "Follow-up question"},
    )
    history = client.get(f"/api/v1/consultations/{consultation_id}/messages")

    assert first.status_code == 200
    assert second.status_code == 200
    assert history.status_code == 200
    assert [item["role"] for item in history.get_json()["items"]] == [
        "USER", "ASSISTANT", "USER", "ASSISTANT"
    ]
    assert history.get_json()["items"][0]["content"] == "First question"
    assert history.get_json()["items"][2]["content"] == "Follow-up question"
    returned_ids = {
        first.get_json()["user_message"]["id"],
        first.get_json()["assistant_message"]["id"],
        second.get_json()["user_message"]["id"],
        second.get_json()["assistant_message"]["id"],
    }
    assert {item["id"] for item in history.get_json()["items"]} == returned_ids


def test_summary_completion_reload_closed_messages_and_restart_full_api_slice(
    persisted_client,
) -> None:
    client, records, _session, _service = persisted_client
    source = records[0]

    exchange = client.post(
        f"/api/v1/consultations/{source.id}/messages",
        json={"content": "My knee hurts after walking."},
    )
    created = client.post(f"/api/v1/consultations/{source.id}/summary")
    repeated = client.post(f"/api/v1/consultations/{source.id}/summary")
    retrieved = client.get(f"/api/v1/consultations/{source.id}/summary")

    assert exchange.status_code == 200
    assert created.status_code == 201
    assert repeated.status_code == 200
    assert retrieved.status_code == 200
    assert repeated.get_json() == created.get_json() == retrieved.get_json()
    assert created.get_json()["consultation_id"] == str(source.id)
    assert created.get_json()["recommended_treatments"]
    assert source.status is ConsultationStatus.COMPLETED
    assert source.recommended_procedure == created.get_json()[
        "recommended_treatments"
    ][0]["treatment"]

    closed = client.post(
        f"/api/v1/consultations/{source.id}/messages",
        json={"content": "Another question"},
    )
    assert closed.status_code == 409
    assert closed.get_json()["code"] == "CONSULTATION_CONVERSATION_CLOSED"

    source_history_before = client.get(
        f"/api/v1/consultations/{source.id}/messages"
    ).get_json()
    restarted = client.post(f"/api/v1/consultations/{source.id}/restart")
    assert restarted.status_code == 201
    restarted_body = restarted.get_json()
    assert restarted_body["id"] != str(source.id)
    assert restarted_body["patient_name"] == source.patient_name
    assert restarted_body["primary_concern"] == source.primary_concern
    assert restarted_body["recommended_procedure"] == ""
    assert restarted_body["status"] == "PENDING"

    restarted_history = client.get(
        f"/api/v1/consultations/{restarted_body['id']}/messages"
    )
    restarted_summary = client.get(
        f"/api/v1/consultations/{restarted_body['id']}/summary"
    )
    assert restarted_history.get_json() == {"items": []}
    assert restarted_summary.status_code == 409
    assert restarted_summary.get_json()["code"] == "SUMMARY_NOT_AVAILABLE"
    assert client.get(
        f"/api/v1/consultations/{source.id}/messages"
    ).get_json() == source_history_before
    assert client.get(
        f"/api/v1/consultations/{source.id}/summary"
    ).get_json() == created.get_json()


def test_appointment_booking_persists_booked_and_preserves_source_data(
    persisted_client,
) -> None:
    client, records, session, service = persisted_client
    source = records[0]

    exchange = client.post(
        f"/api/v1/consultations/{source.id}/messages",
        json={"content": "My knee hurts after walking."},
    )
    summary = client.post(f"/api/v1/consultations/{source.id}/summary")
    assert exchange.status_code == 200
    assert summary.status_code == 201
    summary_before = summary.get_json()
    messages_before = client.get(
        f"/api/v1/consultations/{source.id}/messages"
    ).get_json()
    projection_before = source.recommended_procedure
    recommendation_id = summary_before["recommended_treatments"][0]["id"]

    strict_ai = Mock()
    strict_ai.generate_response.side_effect = AssertionError("booking called AI")
    strict_ai.generate_summary.side_effect = AssertionError("booking called AI")
    service._ai_service = strict_ai

    created = client.post(
        f"/api/v1/consultations/{source.id}/appointments",
        json={
            "recommendation_id": recommendation_id,
            "scheduled_at": "2026-08-20T19:30:00+05:00",
            "location": "  Downtown Clinic  ",
        },
    )

    assert created.status_code == 201
    body = created.get_json()
    assert body["consultation_id"] == str(source.id)
    assert body["recommendation"] == {
        "id": recommendation_id,
        "treatment": summary_before["recommended_treatments"][0]["treatment"],
    }
    assert body["scheduled_at"] == "2026-08-20T14:30:00Z"
    assert body["location"] == "Downtown Clinic"

    session.expire_all()
    persisted = session.query(Appointment).filter_by(consultation_id=source.id).one()
    assert str(persisted.recommendation_id) == recommendation_id
    assert persisted.scheduled_at == datetime(2026, 8, 20, 14, 30, tzinfo=UTC)
    assert source.status is ConsultationStatus.BOOKED
    assert source.recommended_procedure == projection_before
    detail = client.get(f"/api/v1/consultations/{source.id}").get_json()
    assert detail["status"] == "BOOKED"
    assert client.get(
        f"/api/v1/consultations/{source.id}/summary"
    ).get_json() == summary_before
    assert client.get(
        f"/api/v1/consultations/{source.id}/messages"
    ).get_json() == messages_before
    strict_ai.generate_response.assert_not_called()
    strict_ai.generate_summary.assert_not_called()

    repeated = client.post(
        f"/api/v1/consultations/{source.id}/appointments",
        json={
            "recommendation_id": recommendation_id,
            "scheduled_at": "2026-08-21T14:30:00Z",
            "location": "Other Clinic",
        },
    )
    assert repeated.status_code == 409
    assert repeated.get_json()["code"] == "APPOINTMENT_ALREADY_EXISTS"


def test_persisted_booking_rejects_pending_and_cross_consultation_recommendation(
    persisted_client,
) -> None:
    client, records, session, service = persisted_client
    pending, _booked, completed = records

    pending_response = client.post(
        f"/api/v1/consultations/{pending.id}/appointments",
        json={
            "recommendation_id": str(uuid4()),
            "scheduled_at": "2026-08-20T14:30:00Z",
            "location": "Clinic",
        },
    )
    assert pending_response.status_code == 409
    assert pending_response.get_json()["code"] == "CONSULTATION_NOT_BOOKABLE"

    foreign_consultation = Consultation(
        patient_name="Dina Noor",
        primary_concern="Back pain",
        recommended_procedure="Exercise program",
        status=ConsultationStatus.COMPLETED,
    )
    session.add(foreign_consultation)
    session.flush()
    completed_summary = ConsultationSummary(
        consultation_id=completed.id,
        patient_summary="Shoulder stiffness summary",
    )
    foreign_summary = ConsultationSummary(
        consultation_id=foreign_consultation.id,
        patient_summary="Back pain summary",
    )
    session.add_all([completed_summary, foreign_summary])
    session.flush()
    foreign_recommendation = ConsultationRecommendation(
        summary_id=foreign_summary.id,
        treatment="Exercise program",
        position=1,
    )
    session.add(foreign_recommendation)
    session.commit()

    strict_ai = Mock()
    strict_ai.generate_response.side_effect = AssertionError("booking called AI")
    strict_ai.generate_summary.side_effect = AssertionError("booking called AI")
    service._ai_service = strict_ai
    cross_response = client.post(
        f"/api/v1/consultations/{completed.id}/appointments",
        json={
            "recommendation_id": str(foreign_recommendation.id),
            "scheduled_at": "2026-08-20T14:30:00Z",
            "location": "Clinic",
        },
    )

    assert cross_response.status_code == 409
    assert cross_response.get_json() == {
        "error": "Recommendation is not bookable",
        "code": "RECOMMENDATION_NOT_BOOKABLE",
    }
    assert (
        session.query(Appointment).filter_by(consultation_id=completed.id).count()
        == 0
    )
    session.refresh(completed)
    assert completed.status is ConsultationStatus.COMPLETED
    strict_ai.generate_response.assert_not_called()
    strict_ai.generate_summary.assert_not_called()
