"""DN-002 PostgreSQL dashboard repository coverage."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import event, func, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.consultation_models import (
    Appointment,
    Consultation,
    ConsultationRecommendation,
    ConsultationStatus,
    ConsultationSummary,
    Message,
    MessageRole,
)
from app.infrastructure.database import create_database_engine, create_session_factory
from app.repositories.dashboard_repository import DashboardCounts, DashboardRepository


BACKEND_ROOT = Path(__file__).resolve().parents[1]
SCHEDULED_AT = datetime(2026, 8, 20, 14, 30, tzinfo=timezone.utc)


@pytest.fixture(scope="module")
def migrated_database_url(postgresql_url: str) -> str:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", postgresql_url)
    command.upgrade(config, "head")
    return postgresql_url


@pytest.fixture
def database(migrated_database_url: str):
    engine = create_database_engine(migrated_database_url)
    factory = create_session_factory(engine)
    _clean(factory)
    yield engine, factory
    _clean(factory)
    engine.dispose()


def _clean(factory: sessionmaker[Session]) -> None:
    with factory.begin() as session:
        session.execute(text("DELETE FROM appointments"))
        session.execute(text("DELETE FROM consultation_recommendations"))
        session.execute(text("DELETE FROM consultation_summaries"))
        session.execute(text("DELETE FROM messages"))
        session.execute(text("DELETE FROM consultations"))


def _consultation(status: ConsultationStatus, *, label: str) -> Consultation:
    return Consultation(
        id=uuid4(),
        patient_name=label,
        primary_concern="Persistent knee pain",
        recommended_procedure="Physical therapy assessment",
        status=status,
    )


def _add_lineage(
    session: Session,
    consultation: Consultation,
    *,
    message_count: int = 0,
    recommendation_count: int = 1,
) -> ConsultationRecommendation:
    session.add(consultation)
    session.flush()
    session.add_all(
        Message(
            id=uuid4(),
            consultation_id=consultation.id,
            role=MessageRole.USER,
            content=f"Message {index}",
        )
        for index in range(message_count)
    )
    summary = ConsultationSummary(
        id=uuid4(),
        consultation_id=consultation.id,
        patient_summary="Persisted summary",
        recommendation_rationale="Persisted rationale",
    )
    session.add(summary)
    session.flush()
    recommendations = [
        ConsultationRecommendation(
            id=uuid4(),
            summary_id=summary.id,
            treatment=f"Treatment {position}",
            position=position,
        )
        for position in range(1, recommendation_count + 1)
    ]
    session.add_all(recommendations)
    session.flush()
    return recommendations[0]


def _add_appointment(
    session: Session,
    consultation: Consultation,
    recommendation: ConsultationRecommendation,
) -> Appointment:
    appointment = Appointment(
        id=uuid4(),
        consultation_id=consultation.id,
        recommendation_id=recommendation.id,
        scheduled_at=SCHEDULED_AT,
        location="Downtown Clinic",
    )
    session.add(appointment)
    return appointment


def _snapshot(session: Session) -> dict[str, tuple[tuple[object, ...], ...]]:
    tables = (
        Consultation.__table__,
        Message.__table__,
        ConsultationSummary.__table__,
        ConsultationRecommendation.__table__,
        Appointment.__table__,
    )
    return {
        table.name: tuple(
            tuple(row)
            for row in session.execute(
                select(*table.c).order_by(table.c.id)
            ).all()
        )
        for table in tables
    }


def test_empty_database_returns_immutable_integer_zero_counts(database) -> None:
    _, factory = database
    with factory() as session:
        counts = DashboardRepository(session).get_counts()

    assert counts == DashboardCounts(0, 0)
    assert type(counts.total_consultations) is int
    assert type(counts.booked_appointments) is int
    with pytest.raises(AttributeError):
        counts.total_consultations = 1  # type: ignore[misc]


@pytest.mark.parametrize(
    "status",
    [
        ConsultationStatus.PENDING,
        ConsultationStatus.COMPLETED,
        ConsultationStatus.BOOKED,
    ],
)
def test_each_consultation_status_counts_without_an_appointment(
    database, status: ConsultationStatus
) -> None:
    _, factory = database
    with factory.begin() as session:
        session.add(_consultation(status, label=status.value))

    with factory() as session:
        assert DashboardRepository(session).get_counts() == DashboardCounts(1, 0)


def test_mixed_statuses_and_persisted_appointments_are_counted_independently(
    database,
) -> None:
    _, factory = database
    consultations = [
        _consultation(ConsultationStatus.PENDING, label="Pending"),
        _consultation(ConsultationStatus.COMPLETED, label="Completed A"),
        _consultation(ConsultationStatus.COMPLETED, label="Completed B"),
        _consultation(ConsultationStatus.BOOKED, label="Status only"),
        _consultation(ConsultationStatus.BOOKED, label="Appointment backed"),
    ]
    with factory.begin() as session:
        recommendations = [
            _add_lineage(session, consultation) for consultation in consultations
        ]
        _add_appointment(session, consultations[1], recommendations[1])
        _add_appointment(session, consultations[4], recommendations[4])

    with factory() as session:
        assert DashboardRepository(session).get_counts() == DashboardCounts(5, 2)


def test_related_rows_do_not_multiply_either_count(database) -> None:
    _, factory = database
    first = _consultation(ConsultationStatus.BOOKED, label="First")
    second = _consultation(ConsultationStatus.COMPLETED, label="Second")
    with factory.begin() as session:
        first_recommendation = _add_lineage(
            session, first, message_count=4, recommendation_count=3
        )
        _add_lineage(session, second, message_count=2, recommendation_count=2)
        _add_appointment(session, first, first_recommendation)

    with factory() as session:
        assert DashboardRepository(session).get_counts() == DashboardCounts(2, 1)


def test_get_counts_executes_one_non_joining_read_statement(database) -> None:
    engine, factory = database
    statements: list[str] = []

    def capture_statement(
        _connection, _cursor, statement, _parameters, _context, _executemany
    ) -> None:
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", capture_statement)
    try:
        with factory() as session:
            assert DashboardRepository(session).get_counts() == DashboardCounts(0, 0)
    finally:
        event.remove(engine, "before_cursor_execute", capture_statement)

    assert len(statements) == 1
    normalized = " ".join(statements[0].lower().split())
    assert normalized.count("count(") == 2
    assert " from consultations" in normalized
    assert " from appointments" in normalized
    assert " join " not in normalized


def test_get_counts_neither_mutates_nor_commits_and_fresh_session_is_unchanged(
    database, monkeypatch
) -> None:
    _, factory = database
    consultation = _consultation(ConsultationStatus.BOOKED, label="Read only")
    with factory.begin() as session:
        recommendation = _add_lineage(
            session, consultation, message_count=2, recommendation_count=2
        )
        _add_appointment(session, consultation, recommendation)

    with factory() as session:
        before = _snapshot(session)

        def fail_if_called() -> None:
            raise AssertionError("dashboard reads must not commit")

        monkeypatch.setattr(session, "commit", fail_if_called)
        assert DashboardRepository(session).get_counts() == DashboardCounts(1, 1)
        assert not session.new
        assert not session.dirty
        assert not session.deleted
        assert _snapshot(session) == before

    with factory() as fresh_session:
        assert _snapshot(fresh_session) == before
        assert fresh_session.scalar(select(func.count(Consultation.id))) == 1
        assert fresh_session.scalar(select(func.count(Appointment.id))) == 1
