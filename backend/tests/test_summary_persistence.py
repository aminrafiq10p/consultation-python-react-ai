"""CS-002 PostgreSQL summary/recommendation schema and mapping coverage."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError

from app.infrastructure.consultation_models import (
    Consultation,
    ConsultationRecommendation,
    ConsultationStatus,
    ConsultationSummary,
    Message,
    MessageRole,
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

    with session_factory.begin() as session:
        session.execute(text("DELETE FROM consultation_recommendations"))
        session.execute(text("DELETE FROM consultation_summaries"))
        session.execute(text("DELETE FROM messages"))
        session.execute(text("DELETE FROM consultations"))

    yield engine, session_factory

    with session_factory.begin() as session:
        session.execute(text("DELETE FROM consultation_recommendations"))
        session.execute(text("DELETE FROM consultation_summaries"))
        session.execute(text("DELETE FROM messages"))
        session.execute(text("DELETE FROM consultations"))
    engine.dispose()


def _consultation() -> Consultation:
    return Consultation(
        patient_name="Ada Lovelace",
        primary_concern="Persistent knee pain",
        recommended_procedure="",
        status=ConsultationStatus.PENDING,
    )


def _persist_consultation(session_factory) -> Consultation:
    consultation = _consultation()
    with session_factory.begin() as session:
        session.add(consultation)
    return consultation


def _persist_summary(session_factory, consultation_id: UUID) -> ConsultationSummary:
    summary = ConsultationSummary(
        consultation_id=consultation_id,
        patient_summary="The patient described persistent knee pain.",
        recommendation_rationale=None,
    )
    with session_factory.begin() as session:
        session.add(summary)
    return summary


def test_migration_upgrade_downgrade_preserves_feature_001_and_002(
    postgresql_url: str,
) -> None:
    config = _alembic_config(postgresql_url)
    command.downgrade(config, "base")
    command.upgrade(config, "20260813_02")
    engine = create_database_engine(postgresql_url)

    consultation_id = uuid4()
    message_id = uuid4()
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO consultations "
                "(id, patient_name, primary_concern, recommended_procedure, status) "
                "VALUES (:id, 'Ada', 'Knee pain', '', 'PENDING')"
            ),
            {"id": consultation_id},
        )
        connection.execute(
            text(
                "INSERT INTO messages (id, consultation_id, role, content) "
                "VALUES (:id, :consultation_id, 'USER', 'Persistent pain')"
            ),
            {"id": message_id, "consultation_id": consultation_id},
        )

    command.upgrade(config, "head")
    inspector = inspect(engine)
    assert {"consultation_summaries", "consultation_recommendations"}.issubset(
        inspector.get_table_names()
    )
    summary_columns = {
        column["name"]: column
        for column in inspector.get_columns("consultation_summaries")
    }
    recommendation_columns = {
        column["name"]: column
        for column in inspector.get_columns("consultation_recommendations")
    }
    assert set(summary_columns) == {
        "id",
        "consultation_id",
        "patient_summary",
        "recommendation_rationale",
        "created_at",
    }
    assert set(recommendation_columns) == {
        "id",
        "summary_id",
        "treatment",
        "position",
    }
    assert str(summary_columns["id"]["type"]) == "UUID"
    assert str(recommendation_columns["id"]["type"]) == "UUID"
    assert summary_columns["created_at"]["type"].timezone is True
    assert summary_columns["created_at"]["default"] is not None
    summary_foreign_key = inspector.get_foreign_keys("consultation_summaries")[0]
    recommendation_foreign_key = inspector.get_foreign_keys(
        "consultation_recommendations"
    )[0]
    assert summary_foreign_key["referred_table"] == "consultations"
    assert recommendation_foreign_key["referred_table"] == "consultation_summaries"
    assert summary_foreign_key["options"].get("ondelete") is None
    assert recommendation_foreign_key["options"].get("ondelete") is None
    assert {item["name"] for item in inspector.get_unique_constraints(
        "consultation_summaries"
    )} == {"uq_consultation_summaries_consultation_id"}
    assert {item["name"] for item in inspector.get_unique_constraints(
        "consultation_recommendations"
    )} == {"uq_consultation_recommendations_summary_position"}
    assert {item["name"] for item in inspector.get_check_constraints(
        "consultation_summaries"
    )} == {
        "ck_consultation_summaries_patient_summary_nonblank",
        "ck_consultation_summaries_rationale_nonblank",
    }
    assert {item["name"] for item in inspector.get_check_constraints(
        "consultation_recommendations"
    )} == {
        "ck_consultation_recommendations_position_positive",
        "ck_consultation_recommendations_treatment_nonblank",
    }

    command.downgrade(config, "20260813_02")
    downgraded_tables = inspect(engine).get_table_names()
    assert "consultation_summaries" not in downgraded_tables
    assert "consultation_recommendations" not in downgraded_tables
    with engine.connect() as connection:
        assert connection.scalar(
            text("SELECT count(*) FROM consultations WHERE id = :id"),
            {"id": consultation_id},
        ) == 1
        assert connection.scalar(
            text("SELECT count(*) FROM messages WHERE id = :id"),
            {"id": message_id},
        ) == 1

    command.upgrade(config, "head")
    engine.dispose()


def test_uuid_foreign_keys_and_stable_fresh_session_retrieval(database) -> None:
    _, session_factory = database
    consultation = _persist_consultation(session_factory)
    summary = ConsultationSummary(
        id=uuid4(),
        consultation_id=consultation.id,
        patient_summary="The patient described persistent knee pain.",
        recommendation_rationale="Conservative options fit the reported symptoms.",
    )
    first = ConsultationRecommendation(
        summary_id=summary.id,
        treatment="Physical therapy assessment",
        position=1,
    )
    second = ConsultationRecommendation(
        summary_id=summary.id,
        treatment="Clinician follow-up",
        position=2,
    )
    with session_factory.begin() as session:
        session.add(summary)
        session.flush()
        session.add_all([second, first])

    with session_factory() as fresh_session:
        stored_summary = fresh_session.get(ConsultationSummary, summary.id)
        recommendations = fresh_session.scalars(
            select(ConsultationRecommendation)
            .where(ConsultationRecommendation.summary_id == summary.id)
            .order_by(ConsultationRecommendation.position)
        ).all()

    assert stored_summary is not None
    assert isinstance(stored_summary.id, UUID)
    assert stored_summary.consultation_id == consultation.id
    assert stored_summary.created_at.tzinfo is not None
    assert [item.id for item in recommendations] == [first.id, second.id]
    assert all(isinstance(item.id, UUID) for item in recommendations)
    assert [item.treatment for item in recommendations] == [
        "Physical therapy assessment",
        "Clinician follow-up",
    ]

    with session_factory() as session:
        session.add(
            ConsultationSummary(
                consultation_id=uuid4(),
                patient_summary="Unlinked summary",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()

    with session_factory() as session:
        session.add(
            ConsultationRecommendation(
                summary_id=uuid4(), treatment="Unlinked treatment", position=1
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_one_summary_per_consultation_is_enforced(database) -> None:
    _, session_factory = database
    consultation = _persist_consultation(session_factory)
    _persist_summary(session_factory, consultation.id)

    with session_factory() as session:
        session.add(
            ConsultationSummary(
                consultation_id=consultation.id,
                patient_summary="A second summary is forbidden.",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


@pytest.mark.parametrize("patient_summary", ["", "   "])
def test_patient_summary_must_be_nonblank(database, patient_summary: str) -> None:
    _, session_factory = database
    consultation = _persist_consultation(session_factory)
    with session_factory() as session:
        session.add(
            ConsultationSummary(
                consultation_id=consultation.id,
                patient_summary=patient_summary,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_rationale_is_nullable_but_must_be_nonblank_when_present(database) -> None:
    _, session_factory = database
    consultation = _persist_consultation(session_factory)
    summary = _persist_summary(session_factory, consultation.id)
    with session_factory() as session:
        assert session.get(ConsultationSummary, summary.id).recommendation_rationale is None

    second_consultation = _consultation()
    with session_factory.begin() as session:
        session.add(second_consultation)
    with session_factory() as session:
        session.add(
            ConsultationSummary(
                consultation_id=second_consultation.id,
                patient_summary="Valid summary",
                recommendation_rationale="   ",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


@pytest.mark.parametrize("treatment", ["", "   "])
def test_recommendation_treatment_must_be_nonblank(database, treatment: str) -> None:
    _, session_factory = database
    consultation = _persist_consultation(session_factory)
    summary = _persist_summary(session_factory, consultation.id)
    with session_factory() as session:
        session.add(
            ConsultationRecommendation(
                summary_id=summary.id, treatment=treatment, position=1
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


@pytest.mark.parametrize("position", [0, -1])
def test_recommendation_position_must_be_positive(database, position: int) -> None:
    _, session_factory = database
    consultation = _persist_consultation(session_factory)
    summary = _persist_summary(session_factory, consultation.id)
    with session_factory() as session:
        session.add(
            ConsultationRecommendation(
                summary_id=summary.id, treatment="Physical therapy", position=position
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_recommendation_position_is_unique_per_summary(database) -> None:
    _, session_factory = database
    first_consultation = _persist_consultation(session_factory)
    first_summary = _persist_summary(session_factory, first_consultation.id)
    second_consultation = _persist_consultation(session_factory)
    second_summary = _persist_summary(session_factory, second_consultation.id)

    with session_factory.begin() as session:
        session.add_all(
            [
                ConsultationRecommendation(
                    summary_id=first_summary.id, treatment="First", position=1
                ),
                ConsultationRecommendation(
                    summary_id=second_summary.id, treatment="Allowed", position=1
                ),
            ]
        )
    with session_factory() as session:
        session.add(
            ConsultationRecommendation(
                summary_id=first_summary.id, treatment="Duplicate", position=1
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_foreign_keys_do_not_delete_cascade(database) -> None:
    _, session_factory = database
    consultation = _persist_consultation(session_factory)
    summary = _persist_summary(session_factory, consultation.id)
    with session_factory.begin() as session:
        session.add(
            ConsultationRecommendation(
                summary_id=summary.id, treatment="Physical therapy", position=1
            )
        )

    with session_factory() as session:
        session.delete(session.get(Consultation, consultation.id))
        with pytest.raises(IntegrityError):
            session.commit()
    with session_factory() as session:
        assert session.get(ConsultationSummary, summary.id) is not None
        session.delete(session.get(ConsultationSummary, summary.id))
        with pytest.raises(IntegrityError):
            session.commit()


def test_consultation_and_message_persistence_remain_usable(database) -> None:
    _, session_factory = database
    consultation = _persist_consultation(session_factory)
    message = Message(
        consultation_id=consultation.id,
        role=MessageRole.USER,
        content="My knee still hurts.",
    )
    with session_factory.begin() as session:
        session.add(message)

    with session_factory() as fresh_session:
        stored_consultation = fresh_session.get(Consultation, consultation.id)
        stored_message = fresh_session.get(Message, message.id)
    assert stored_consultation is not None
    assert stored_consultation.status is ConsultationStatus.PENDING
    assert stored_message is not None
    assert stored_message.content == "My knee still hurts."
