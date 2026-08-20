"""AB-003 PostgreSQL appointment repository and atomic transaction coverage."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import event, func, select, text
from sqlalchemy.exc import IntegrityError

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
from app.repositories.appointment_repository import (
    APPOINTMENT_CONSULTATION_UNIQUE_CONSTRAINT,
    AppointmentRepository,
)


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


def _clean(factory) -> None:
    with factory.begin() as session:
        session.execute(text("DELETE FROM appointments"))
        session.execute(text("DELETE FROM consultation_recommendations"))
        session.execute(text("DELETE FROM consultation_summaries"))
        session.execute(text("DELETE FROM messages"))
        session.execute(text("DELETE FROM consultations"))


def _persist_lineage(factory, *, label: str = "Ada"):
    consultation = Consultation(
        id=uuid4(),
        patient_name=label,
        primary_concern="Persistent knee pain",
        recommended_procedure="Original projection",
        status=ConsultationStatus.COMPLETED,
    )
    summary = ConsultationSummary(
        id=uuid4(),
        consultation_id=consultation.id,
        patient_summary=f"{label} persisted summary",
        recommendation_rationale="Original rationale",
    )
    recommendations = (
        ConsultationRecommendation(
            id=uuid4(), summary_id=summary.id, treatment="Physical therapy", position=1
        ),
        ConsultationRecommendation(
            id=uuid4(), summary_id=summary.id, treatment="Clinician follow-up", position=2
        ),
    )
    message = Message(
        id=uuid4(),
        consultation_id=consultation.id,
        role=MessageRole.USER,
        content="Original message",
    )
    with factory.begin() as session:
        session.add(consultation)
        session.flush()
        session.add_all([message, summary])
        session.flush()
        session.add_all(recommendations)
    return consultation, summary, recommendations, message


def _create(repository, consultation, recommendation, *, location="Downtown Clinic"):
    return repository.create_appointment(
        consultation,
        recommendation,
        scheduled_at=SCHEDULED_AT,
        location=location,
    )


def test_list_appointments_returns_empty_for_no_persisted_rows(database) -> None:
    _, factory = database
    with factory() as session:
        assert AppointmentRepository(session).list_appointments() == []


def test_list_appointments_projects_patient_and_selected_treatment(database) -> None:
    _, factory = database
    consultation, _, recommendations, _ = _persist_lineage(factory)
    with factory() as session:
        repository = AppointmentRepository(session)
        appointment = Appointment(
            id=uuid4(),
            consultation_id=consultation.id,
            recommendation_id=recommendations[1].id,
            scheduled_at=SCHEDULED_AT,
            location="Downtown Clinic",
        )
        session.add(appointment)
        session.commit()

        items = repository.list_appointments()

    assert len(items) == 1
    item = items[0]
    assert item.id == appointment.id
    assert item.consultation_id == consultation.id
    assert item.patient_name == "Ada"
    assert item.recommendation_id == recommendations[1].id
    assert item.treatment == "Clinician follow-up"
    assert item.scheduled_at == SCHEDULED_AT
    assert item.location == "Downtown Clinic"
    assert item.created_at.tzinfo is not None


def test_list_appointments_rejects_cross_consultation_recommendation_lineage(
    database,
) -> None:
    _, factory = database
    consultation, _, _, _ = _persist_lineage(factory, label="Owner")
    other_consultation, _, other_recommendations, _ = _persist_lineage(
        factory, label="Other"
    )
    assert consultation.id != other_consultation.id

    with factory() as session:
        session.add(
            Appointment(
                consultation_id=consultation.id,
                recommendation_id=other_recommendations[0].id,
                scheduled_at=SCHEDULED_AT,
                location="Downtown Clinic",
            )
        )
        session.commit()

        items = AppointmentRepository(session).list_appointments()

    assert items == []


def test_list_appointments_orders_by_schedule_then_id(database) -> None:
    _, factory = database
    first, _, first_recommendations, _ = _persist_lineage(factory, label="First")
    second, _, second_recommendations, _ = _persist_lineage(factory, label="Second")
    earlier_id = UUID("00000000-0000-4000-8000-000000000001")
    later_id = UUID("00000000-0000-4000-8000-000000000002")
    with factory() as session:
        session.add_all(
            [
                Appointment(
                    id=later_id,
                    consultation_id=first.id,
                    recommendation_id=first_recommendations[0].id,
                    scheduled_at=SCHEDULED_AT,
                    location="Later ID Clinic",
                ),
                Appointment(
                    id=earlier_id,
                    consultation_id=second.id,
                    recommendation_id=second_recommendations[0].id,
                    scheduled_at=SCHEDULED_AT,
                    location="Earlier ID Clinic",
                ),
            ]
        )
        session.commit()
        items = AppointmentRepository(session).list_appointments()

    assert [item.id for item in items] == [earlier_id, later_id]


def test_list_appointments_uses_one_query_and_does_not_mutate(database) -> None:
    engine, factory = database
    consultation, _, recommendations, _ = _persist_lineage(factory)
    with factory() as session:
        session.add(
            Appointment(
                consultation_id=consultation.id,
                recommendation_id=recommendations[0].id,
                scheduled_at=SCHEDULED_AT,
                location="Downtown Clinic",
            )
        )
        session.commit()
        statements: list[str] = []

        def record_statement(
            _conn, _cursor, statement, _parameters, _context, _executemany
        ):
            statements.append(statement)

        event.listen(engine, "before_cursor_execute", record_statement)
        try:
            items = AppointmentRepository(session).list_appointments()
        finally:
            event.remove(engine, "before_cursor_execute", record_statement)

        assert len(items) == 1
        assert len(statements) == 1
        assert statements[0].lstrip().upper().startswith("SELECT")
        assert not session.new
        assert not session.dirty
        assert not session.deleted


def test_lookup_is_none_then_returns_persisted_appointment(database) -> None:
    _, factory = database
    consultation, _, recommendations, _ = _persist_lineage(factory)
    with factory() as session:
        repository = AppointmentRepository(session)
        assert repository.get_appointment(consultation.id) is None
        locked = repository.lock_consultation(consultation.id)
        recommendation = repository.get_recommendation(recommendations[0].id)
        assert locked is not None and recommendation is not None
        created = _create(repository, locked, recommendation)

    with factory() as fresh_session:
        stored = AppointmentRepository(fresh_session).get_appointment(consultation.id)
        assert stored is not None
        assert stored.id == created.aggregate.appointment.id
        assert isinstance(stored.id, UUID)


def test_lock_query_uses_for_update_and_session_remains_usable_after_abort(
    database,
) -> None:
    engine, factory = database
    consultation, _, _, _ = _persist_lineage(factory)
    statement = (
        select(Consultation)
        .where(Consultation.id == consultation.id)
        .with_for_update()
    )
    assert "FOR UPDATE" in str(statement.compile(dialect=engine.dialect))
    with factory() as session:
        repository = AppointmentRepository(session)
        assert repository.lock_consultation(consultation.id) is not None
        repository.abort()
        assert repository.get_appointment(consultation.id) is None


def test_summary_and_recommendation_reads_distinguish_ownership(database) -> None:
    _, factory = database
    first, first_summary, first_recommendations, _ = _persist_lineage(factory)
    second, _, second_recommendations, _ = _persist_lineage(factory, label="Grace")
    with factory() as session:
        repository = AppointmentRepository(session)
        assert repository.get_summary(first.id).id == first_summary.id
        assert repository.get_recommendation(first_recommendations[0].id) is not None
        assert (
            repository.get_owned_recommendation(first.id, first_recommendations[0].id)
            is not None
        )
        assert repository.get_recommendation(second_recommendations[0].id) is not None
        assert (
            repository.get_owned_recommendation(first.id, second_recommendations[0].id)
            is None
        )
        missing = uuid4()
        assert repository.get_recommendation(missing) is None
        assert repository.get_owned_recommendation(second.id, missing) is None


def test_atomic_creation_reloads_projection_and_preserves_source_data(database) -> None:
    _, factory = database
    consultation, summary, recommendations, message = _persist_lineage(factory)
    with factory() as session:
        repository = AppointmentRepository(session)
        locked = repository.lock_consultation(consultation.id)
        owned = repository.get_owned_recommendation(
            consultation.id, recommendations[1].id
        )
        assert locked is not None and owned is not None
        result = _create(repository, locked, owned)
        assert result.created is True
        assert result.aggregate.recommendation.id == recommendations[1].id
        assert result.aggregate.recommendation.treatment == "Clinician follow-up"

    with factory() as session:
        stored = session.get(Appointment, result.aggregate.appointment.id)
        current_consultation = session.get(Consultation, consultation.id)
        current_summary = session.get(ConsultationSummary, summary.id)
        current_message = session.get(Message, message.id)
        current_recommendations = session.scalars(
            select(ConsultationRecommendation)
            .where(ConsultationRecommendation.summary_id == summary.id)
            .order_by(ConsultationRecommendation.position)
        ).all()
        assert stored is not None and stored.created_at.tzinfo is not None
        assert current_consultation.status is ConsultationStatus.BOOKED
        assert current_consultation.recommended_procedure == "Original projection"
        assert current_summary.patient_summary == "Ada persisted summary"
        assert current_summary.recommendation_rationale == "Original rationale"
        assert current_message.content == "Original message"
        assert [(item.id, item.treatment, item.position) for item in current_recommendations] == [
            (recommendations[0].id, "Physical therapy", 1),
            (recommendations[1].id, "Clinician follow-up", 2),
        ]


def test_forced_commit_failure_rolls_back_appointment_and_status(
    database, monkeypatch
) -> None:
    _, factory = database
    consultation, _, recommendations, _ = _persist_lineage(factory)
    with factory() as session:
        repository = AppointmentRepository(session)
        locked = repository.lock_consultation(consultation.id)
        owned = repository.get_recommendation(recommendations[0].id)
        assert locked is not None and owned is not None

        def fail_commit():
            raise RuntimeError("forced commit failure")

        monkeypatch.setattr(session, "commit", fail_commit)
        with pytest.raises(RuntimeError, match="forced commit failure"):
            _create(repository, locked, owned)

    with factory() as fresh_session:
        assert fresh_session.scalar(select(func.count(Appointment.id))) == 0
        stored = fresh_session.get(Consultation, consultation.id)
        assert stored is not None and stored.status is ConsultationStatus.COMPLETED


def test_exact_duplicate_constraint_is_reconciled(database) -> None:
    _, factory = database
    consultation, _, recommendations, _ = _persist_lineage(factory)
    with factory() as first_session:
        repository = AppointmentRepository(first_session)
        attached = repository.lock_consultation(consultation.id)
        recommendation = repository.get_recommendation(recommendations[0].id)
        assert attached is not None and recommendation is not None
        winner = _create(repository, attached, recommendation)

    with factory() as losing_session:
        repository = AppointmentRepository(losing_session)
        attached = losing_session.get(Consultation, consultation.id)
        recommendation = repository.get_recommendation(recommendations[1].id)
        assert attached is not None and recommendation is not None
        recovered = _create(repository, attached, recommendation)
        assert recovered.created is False
        assert recovered.aggregate.appointment.id == winner.aggregate.appointment.id
    assert APPOINTMENT_CONSULTATION_UNIQUE_CONSTRAINT == (
        "uq_appointments_consultation_id"
    )


def test_unrelated_integrity_error_is_not_misclassified(database) -> None:
    _, factory = database
    consultation, _, recommendations, _ = _persist_lineage(factory)
    with factory() as session:
        repository = AppointmentRepository(session)
        attached = repository.lock_consultation(consultation.id)
        recommendation = repository.get_recommendation(recommendations[0].id)
        assert attached is not None and recommendation is not None
        with pytest.raises(IntegrityError) as caught:
            _create(repository, attached, recommendation, location="   ")
        assert repository._constraint_name(caught.value) != (
            APPOINTMENT_CONSULTATION_UNIQUE_CONSTRAINT
        )
        assert repository.get_appointment(consultation.id) is None


def test_concurrent_locked_attempts_leave_one_consistent_winner(database) -> None:
    _, factory = database
    consultation, _, recommendations, _ = _persist_lineage(factory)
    barrier = Barrier(2)

    def attempt(recommendation_id: UUID):
        with factory() as session:
            repository = AppointmentRepository(session)
            barrier.wait(timeout=10)
            locked = repository.lock_consultation(consultation.id)
            assert locked is not None
            existing = repository.get_appointment(consultation.id)
            if existing is not None:
                repository.abort()
                return False, existing.id
            recommendation = repository.get_owned_recommendation(
                consultation.id, recommendation_id
            )
            assert recommendation is not None
            result = _create(repository, locked, recommendation)
            return result.created, result.aggregate.appointment.id

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, [item.id for item in recommendations]))

    assert sorted(created for created, _ in results) == [False, True]
    assert results[0][1] == results[1][1]
    with factory() as session:
        assert session.scalar(select(func.count(Appointment.id))) == 1
        stored = session.get(Consultation, consultation.id)
        assert stored is not None and stored.status is ConsultationStatus.BOOKED
