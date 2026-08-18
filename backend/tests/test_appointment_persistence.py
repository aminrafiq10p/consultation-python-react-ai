"""AB-002 PostgreSQL appointment schema and mapping coverage."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.exc import DataError, IntegrityError

from app.infrastructure.consultation_models import (
    Appointment,
    Consultation,
    ConsultationRecommendation,
    ConsultationStatus,
    ConsultationSummary,
)
from app.infrastructure.database import create_database_engine, create_session_factory


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _alembic_config(database_url: str) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


@pytest.fixture(scope="module")
def migrated_database_url(postgresql_url: str) -> str:
    command.upgrade(_alembic_config(postgresql_url), "head")
    return postgresql_url


@pytest.fixture
def database(migrated_database_url: str):
    engine = create_database_engine(migrated_database_url)
    session_factory = create_session_factory(engine)
    _clean(session_factory)
    yield engine, session_factory
    _clean(session_factory)
    engine.dispose()


def _clean(session_factory) -> None:
    with session_factory.begin() as session:
        session.execute(text("DELETE FROM appointments"))
        session.execute(text("DELETE FROM consultation_recommendations"))
        session.execute(text("DELETE FROM consultation_summaries"))
        session.execute(text("DELETE FROM messages"))
        session.execute(text("DELETE FROM consultations"))


def _persist_lineage(session_factory):
    consultation = Consultation(
        id=uuid4(),
        patient_name="Ada Lovelace",
        primary_concern="Persistent knee pain",
        recommended_procedure="Physical therapy assessment",
        status=ConsultationStatus.COMPLETED,
    )
    summary = ConsultationSummary(
        id=uuid4(),
        consultation_id=consultation.id,
        patient_summary="Persistent knee pain was discussed.",
    )
    recommendation = ConsultationRecommendation(
        summary_id=summary.id,
        treatment="Physical therapy assessment",
        position=1,
    )
    with session_factory.begin() as session:
        session.add(consultation)
        session.flush()
        session.add(summary)
        session.flush()
        session.add(recommendation)
    return consultation, summary, recommendation


def _appointment(consultation_id: UUID, recommendation_id: UUID, **values):
    attributes = {
        "consultation_id": consultation_id,
        "recommendation_id": recommendation_id,
        "scheduled_at": datetime(2026, 8, 20, 14, 30, tzinfo=timezone.utc),
        "location": "Downtown Clinic",
    }
    attributes.update(values)
    return Appointment(**attributes)


def test_migration_upgrade_schema_and_downgrade_preserve_existing_rows(
    postgresql_url: str,
) -> None:
    config = _alembic_config(postgresql_url)
    command.upgrade(config, "20260817_03")
    engine = create_database_engine(postgresql_url)
    consultation_id = uuid4()
    summary_id = uuid4()
    recommendation_id = uuid4()
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO consultations "
                "(id, patient_name, primary_concern, recommended_procedure, status) "
                "VALUES (:id, 'Ada', 'Knee pain', 'Physical therapy', 'COMPLETED')"
            ),
            {"id": consultation_id},
        )
        connection.execute(
            text(
                "INSERT INTO consultation_summaries "
                "(id, consultation_id, patient_summary) "
                "VALUES (:id, :consultation_id, 'Persisted summary')"
            ),
            {"id": summary_id, "consultation_id": consultation_id},
        )
        connection.execute(
            text(
                "INSERT INTO consultation_recommendations "
                "(id, summary_id, treatment, position) "
                "VALUES (:id, :summary_id, 'Physical therapy', 1)"
            ),
            {"id": recommendation_id, "summary_id": summary_id},
        )

    command.upgrade(config, "head")
    inspector = inspect(engine)
    assert "appointments" in inspector.get_table_names()
    columns = {item["name"]: item for item in inspector.get_columns("appointments")}
    assert set(columns) == {
        "id", "consultation_id", "recommendation_id", "scheduled_at",
        "location", "created_at",
    }
    assert str(columns["id"]["type"]) == "UUID"
    assert str(columns["consultation_id"]["type"]) == "UUID"
    assert str(columns["recommendation_id"]["type"]) == "UUID"
    assert columns["scheduled_at"]["type"].timezone is True
    assert columns["created_at"]["type"].timezone is True
    assert columns["created_at"]["default"] is not None
    assert columns["location"]["type"].length == 200
    assert all(not columns[name]["nullable"] for name in columns)
    foreign_keys = {
        item["constrained_columns"][0]: item
        for item in inspector.get_foreign_keys("appointments")
    }
    assert foreign_keys["consultation_id"]["referred_table"] == "consultations"
    assert foreign_keys["recommendation_id"]["referred_table"] == (
        "consultation_recommendations"
    )
    assert all(item["options"].get("ondelete") is None for item in foreign_keys.values())
    assert {item["name"] for item in inspector.get_unique_constraints("appointments")} == {
        "uq_appointments_consultation_id"
    }
    assert {item["name"] for item in inspector.get_check_constraints("appointments")} == {
        "ck_appointments_location_nonblank",
        "ck_appointments_location_max_length",
    }
    assert "ix_appointments_recommendation_id" in {
        item["name"] for item in inspector.get_indexes("appointments")
    }

    command.downgrade(config, "20260817_03")
    assert "appointments" not in inspect(engine).get_table_names()
    with engine.connect() as connection:
        assert connection.scalar(
            text("SELECT count(*) FROM consultations WHERE id = :id"),
            {"id": consultation_id},
        ) == 1
        assert connection.scalar(
            text("SELECT count(*) FROM consultation_recommendations WHERE id = :id"),
            {"id": recommendation_id},
        ) == 1
    command.upgrade(config, "head")
    engine.dispose()


def test_uuid_timestamps_default_and_fresh_session_round_trip(database) -> None:
    _, session_factory = database
    consultation, _, recommendation = _persist_lineage(session_factory)
    scheduled_at = datetime(2026, 8, 20, 19, 30, tzinfo=timezone(timedelta(hours=5)))
    appointment = _appointment(
        consultation.id, recommendation.id, scheduled_at=scheduled_at
    )
    with session_factory.begin() as session:
        session.add(appointment)

    with session_factory() as fresh_session:
        stored = fresh_session.get(Appointment, appointment.id)
    assert stored is not None
    assert isinstance(stored.id, UUID)
    assert stored.consultation_id == consultation.id
    assert stored.recommendation_id == recommendation.id
    assert stored.scheduled_at.tzinfo is not None
    assert stored.scheduled_at == scheduled_at
    assert stored.created_at is not None
    assert stored.created_at.tzinfo is not None
    assert stored.location == "Downtown Clinic"


def test_consultation_and_recommendation_foreign_keys_are_enforced(database) -> None:
    _, session_factory = database
    consultation, _, recommendation = _persist_lineage(session_factory)
    with session_factory() as session:
        session.add(_appointment(uuid4(), recommendation.id))
        with pytest.raises(IntegrityError):
            session.commit()
    with session_factory() as session:
        session.add(_appointment(consultation.id, uuid4()))
        with pytest.raises(IntegrityError):
            session.commit()


def test_one_appointment_per_consultation_is_enforced(database) -> None:
    _, session_factory = database
    consultation, summary, recommendation = _persist_lineage(session_factory)
    second = ConsultationRecommendation(
        summary_id=summary.id, treatment="Clinician follow-up", position=2
    )
    with session_factory.begin() as session:
        session.add(second)
        session.add(_appointment(consultation.id, recommendation.id))
    with session_factory() as session:
        session.add(_appointment(consultation.id, second.id))
        with pytest.raises(IntegrityError):
            session.commit()


def test_scheduled_at_is_required(database) -> None:
    _, session_factory = database
    consultation, _, recommendation = _persist_lineage(session_factory)
    with session_factory() as session:
        session.add(_appointment(consultation.id, recommendation.id, scheduled_at=None))
        with pytest.raises(IntegrityError):
            session.commit()


@pytest.mark.parametrize("location", [None, "", "   "])
def test_location_is_required_and_nonblank(database, location) -> None:
    _, session_factory = database
    consultation, _, recommendation = _persist_lineage(session_factory)
    with session_factory() as session:
        session.add(_appointment(consultation.id, recommendation.id, location=location))
        with pytest.raises(IntegrityError):
            session.commit()


def test_location_longer_than_200_characters_is_rejected(database) -> None:
    _, session_factory = database
    consultation, _, recommendation = _persist_lineage(session_factory)
    with session_factory() as session:
        session.add(_appointment(consultation.id, recommendation.id, location="x" * 201))
        with pytest.raises((DataError, IntegrityError)):
            session.commit()


def test_mapping_and_table_do_not_copy_treatment_or_add_status(database) -> None:
    engine, _ = database
    assert set(Appointment.__table__.columns.keys()) == {
        "id", "consultation_id", "recommendation_id", "scheduled_at",
        "location", "created_at",
    }
    assert "treatment" not in {
        item["name"] for item in inspect(engine).get_columns("appointments")
    }
