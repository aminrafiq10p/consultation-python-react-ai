"""AI-003 focused message repository coverage."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.consultation_models import (
    Consultation,
    ConsultationStatus,
    Message,
    MessageRole,
)
from app.repositories.message_repository import MessageRepository

BACKEND_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def migrated_database_url(postgresql_url: str) -> str:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", postgresql_url)
    command.upgrade(config, "head")
    return postgresql_url


@pytest.fixture
def database(migrated_database_url: str):
    engine = create_engine(migrated_database_url, pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    with session_factory.begin() as session:
        session.execute(text("DELETE FROM messages"))
        session.execute(text("DELETE FROM consultations"))
    yield session_factory
    with session_factory.begin() as session:
        session.execute(text("DELETE FROM messages"))
        session.execute(text("DELETE FROM consultations"))
    engine.dispose()


def _consultation(patient_name: str = "Ada Lovelace") -> Consultation:
    return Consultation(
        patient_name=patient_name,
        primary_concern="Persistent knee pain",
        recommended_procedure="Physical therapy assessment",
        status=ConsultationStatus.PENDING,
    )


def _seed(
    session_factory: sessionmaker[Session], *consultations: Consultation
) -> None:
    with session_factory.begin() as session:
        session.add_all(consultations)


def test_persist_user_returns_identifier_and_survives_fresh_session(database) -> None:
    consultation = _consultation()
    _seed(database, consultation)
    with database() as session:
        message = Message(
            consultation_id=consultation.id,
            role=MessageRole.USER,
            content="What should I expect?",
        )
        persisted = MessageRepository(session).persist_message(message)
        assert persisted is message
        assert isinstance(persisted.id, UUID)
        assert persisted.created_at is not None
        persisted_id = persisted.id

    with database() as fresh_session:
        stored = fresh_session.get(Message, persisted_id)
        assert stored is not None
        assert stored.role is MessageRole.USER
        assert stored.content == "What should I expect?"


def test_persist_assistant_payload_survives_retrieval(database) -> None:
    consultation = _consultation()
    _seed(database, consultation)
    payload = {"items": [{"label": "Duration", "value": "30 minutes"}]}
    with database() as session:
        persisted = MessageRepository(session).persist_message(
            Message(
                consultation_id=consultation.id,
                role=MessageRole.ASSISTANT,
                content="Here is what to expect.",
                structured_payload=payload,
            )
        )
        persisted_id = persisted.id

    with database() as fresh_session:
        stored = MessageRepository(fresh_session).list_messages(consultation.id)
        assert [item.id for item in stored] == [persisted_id]
        assert stored[0].role is MessageRole.ASSISTANT
        assert stored[0].structured_payload == payload


def test_list_messages_is_consultation_scoped_and_empty_when_none(database) -> None:
    requested, other, empty = (
        _consultation("Requested"),
        _consultation("Other"),
        _consultation("Empty"),
    )
    _seed(database, requested, other, empty)
    with database() as session:
        repository = MessageRepository(session)
        expected = repository.persist_message(
            Message(
                consultation_id=requested.id,
                role=MessageRole.USER,
                content="Requested history",
            )
        )
        repository.persist_message(
            Message(
                consultation_id=other.id,
                role=MessageRole.USER,
                content="Other history",
            )
        )
        assert [item.id for item in repository.list_messages(requested.id)] == [
            expected.id
        ]
        assert repository.list_messages(empty.id) == []


def test_list_messages_orders_by_created_at_then_id(database) -> None:
    consultation = _consultation()
    _seed(database, consultation)
    low_id, high_id = sorted((uuid4(), uuid4()), key=lambda value: value.int)
    early_id = uuid4()
    tied_at = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)
    with database.begin() as session:
        session.add_all(
            [
                Message(id=high_id, consultation_id=consultation.id,
                        role=MessageRole.ASSISTANT, content="Tie second", created_at=tied_at),
                Message(id=early_id, consultation_id=consultation.id,
                        role=MessageRole.USER, content="Earlier",
                        created_at=datetime(2026, 8, 13, 11, 0, tzinfo=timezone.utc)),
                Message(id=low_id, consultation_id=consultation.id,
                        role=MessageRole.USER, content="Tie first", created_at=tied_at),
            ]
        )
    with database() as session:
        ordered = MessageRepository(session).list_messages(consultation.id)
    assert [message.id for message in ordered] == [early_id, low_id, high_id]


def test_invalid_user_payload_rolls_back_only_failed_unit(database) -> None:
    consultation = _consultation()
    _seed(database, consultation)
    with database() as session:
        repository = MessageRepository(session)
        committed = repository.persist_message(
            Message(consultation_id=consultation.id, role=MessageRole.USER,
                    content="This committed unit must survive.")
        )
        with pytest.raises(IntegrityError):
            repository.persist_message(
                Message(consultation_id=consultation.id, role=MessageRole.USER,
                        content="Invalid", structured_payload={"not": "allowed"})
            )
        assert [item.id for item in repository.list_messages(consultation.id)] == [
            committed.id
        ]
        after_rollback = repository.persist_message(
            Message(consultation_id=consultation.id, role=MessageRole.ASSISTANT,
                    content="The session remains usable.")
        )

    with database() as fresh_session:
        stored_ids = [
            item.id
            for item in MessageRepository(fresh_session).list_messages(consultation.id)
        ]
    assert stored_ids == [committed.id, after_rollback.id]
