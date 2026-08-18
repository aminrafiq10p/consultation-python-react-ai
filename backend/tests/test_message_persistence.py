"""AI-002 PostgreSQL migration and message mapping coverage."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import DataError, IntegrityError, StatementError

from app.infrastructure.consultation_models import (
    Consultation,
    ConsultationStatus,
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
        session.execute(text("DELETE FROM appointments"))
        session.execute(text("DELETE FROM consultation_recommendations"))
        session.execute(text("DELETE FROM consultation_summaries"))
        session.execute(text("DELETE FROM messages"))
        session.execute(text("DELETE FROM consultations"))

    yield engine, session_factory

    with session_factory.begin() as session:
        session.execute(text("DELETE FROM appointments"))
        session.execute(text("DELETE FROM consultation_recommendations"))
        session.execute(text("DELETE FROM consultation_summaries"))
        session.execute(text("DELETE FROM messages"))
        session.execute(text("DELETE FROM consultations"))
    engine.dispose()


def _consultation() -> Consultation:
    return Consultation(
        patient_name="Ada Lovelace",
        primary_concern="Persistent knee pain",
        recommended_procedure="Physical therapy assessment",
        status=ConsultationStatus.PENDING,
    )


def test_migration_upgrade_downgrade_and_schema(postgresql_url: str) -> None:
    config = _alembic_config(postgresql_url)
    command.upgrade(config, "head")
    engine = create_database_engine(postgresql_url)

    inspector = inspect(engine)
    assert "messages" in inspector.get_table_names()
    message_indexes = inspector.get_indexes("messages")
    assert message_indexes[0]["column_names"] == [
        "consultation_id",
        "created_at",
        "id",
    ]
    assert message_indexes[0]["name"] == (
        "ix_messages_consultation_id_created_at_id"
    )
    assert inspector.get_foreign_keys("messages")[0]["referred_table"] == "consultations"

    command.downgrade(config, "20260813_01")
    assert "messages" not in inspect(engine).get_table_names()
    with engine.connect() as connection:
        enum_exists = connection.scalar(
            text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'message_role')")
        )
    assert enum_exists is False

    command.upgrade(config, "head")
    engine.dispose()


def test_user_and_assistant_messages_persist_and_survive_fresh_session(database) -> None:
    _, session_factory = database
    consultation = _consultation()
    assistant_payload = {"items": [{"label": "Duration", "value": "30 minutes"}]}

    with session_factory.begin() as session:
        session.add(consultation)
        session.flush()
        user_message = Message(
            consultation_id=consultation.id,
            role=MessageRole.USER,
            content="What should I expect?",
        )
        assistant_message = Message(
            consultation_id=consultation.id,
            role=MessageRole.ASSISTANT,
            content="Here is what to expect.",
            structured_payload=assistant_payload,
        )
        session.add_all([user_message, assistant_message])

    with session_factory() as fresh_session:
        stored_user = fresh_session.get(Message, user_message.id)
        stored_assistant = fresh_session.get(Message, assistant_message.id)

        assert stored_user is not None
        assert stored_user.consultation_id == consultation.id
        assert stored_user.role is MessageRole.USER
        assert stored_user.content == "What should I expect?"
        assert stored_user.created_at is not None
        assert stored_user.created_at.tzinfo is not None
        assert stored_assistant is not None
        assert stored_assistant.role is MessageRole.ASSISTANT
        assert stored_assistant.structured_payload == assistant_payload


def test_invalid_consultation_foreign_key_is_rejected(database) -> None:
    _, session_factory = database
    with session_factory() as session:
        session.add(
            Message(
                consultation_id=uuid4(),
                role=MessageRole.USER,
                content="Unlinked message",
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_invalid_role_is_rejected(database) -> None:
    _, session_factory = database
    consultation = _consultation()
    with session_factory.begin() as session:
        session.add(consultation)

    with session_factory() as session:
        with pytest.raises(DataError):
            session.execute(
                text(
                    "INSERT INTO messages (id, consultation_id, role, content) "
                    "VALUES (:id, :consultation_id, :role, :content)"
                ),
                {
                    "id": uuid4(),
                    "consultation_id": consultation.id,
                    "role": "SYSTEM",
                    "content": "Invalid role",
                },
            )


def test_user_structured_payload_is_rejected(database) -> None:
    _, session_factory = database
    consultation = _consultation()
    with session_factory.begin() as session:
        session.add(consultation)

    with session_factory() as session:
        session.add(
            Message(
                consultation_id=consultation.id,
                role=MessageRole.USER,
                content="User content",
                structured_payload={"not": "allowed"},
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_content_is_required(database) -> None:
    _, session_factory = database
    consultation = _consultation()
    with session_factory.begin() as session:
        session.add(consultation)

    with session_factory() as session:
        with pytest.raises(IntegrityError):
            session.execute(
                text(
                    "INSERT INTO messages (id, consultation_id, role, content) "
                    "VALUES (:id, :consultation_id, 'USER', NULL)"
                ),
                {"id": uuid4(), "consultation_id": consultation.id},
            )
            session.commit()


def test_model_rejects_unapproved_role_before_persistence(database) -> None:
    _, session_factory = database
    consultation = _consultation()
    with session_factory.begin() as session:
        session.add(consultation)

    with session_factory() as session:
        session.add(
            Message(
                consultation_id=consultation.id,
                role="SYSTEM",  # type: ignore[arg-type]
                content="Invalid role",
            )
        )
        with pytest.raises(StatementError):
            session.commit()


def test_composite_index_supports_deterministic_tied_timestamp_order(database) -> None:
    _, session_factory = database
    consultation = _consultation()
    lower_id = uuid4()
    higher_id = uuid4()
    if lower_id.int > higher_id.int:
        lower_id, higher_id = higher_id, lower_id

    with session_factory.begin() as session:
        session.add(consultation)
        session.flush()
        session.add_all(
            [
                Message(
                    id=higher_id,
                    consultation_id=consultation.id,
                    role=MessageRole.ASSISTANT,
                    content="Second by UUID",
                ),
                Message(
                    id=lower_id,
                    consultation_id=consultation.id,
                    role=MessageRole.USER,
                    content="First by UUID",
                ),
            ]
        )
        session.flush()
        session.execute(
            text(
                "UPDATE messages SET created_at = '2026-08-13 00:00:00+00' "
                "WHERE consultation_id = :consultation_id"
            ),
            {"consultation_id": consultation.id},
        )

    with session_factory() as session:
        ordered_ids = session.scalars(
            select(Message.id)
            .where(Message.consultation_id == consultation.id)
            .order_by(Message.created_at, Message.id)
        ).all()

    assert ordered_ids == [lower_id, higher_id]
