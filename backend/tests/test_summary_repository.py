"""CS-003 PostgreSQL summary aggregate repository coverage."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.consultation_models import (
    Consultation,
    ConsultationRecommendation,
    ConsultationStatus,
    ConsultationSummary,
)
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.summary_repository import SummaryRepository


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
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    _clean(factory)
    yield factory
    _clean(factory)
    engine.dispose()


def _clean(factory: sessionmaker[Session]) -> None:
    with factory.begin() as session:
        session.execute(text("DELETE FROM consultation_recommendations"))
        session.execute(text("DELETE FROM consultation_summaries"))
        session.execute(text("DELETE FROM messages"))
        session.execute(text("DELETE FROM consultations"))


def _new_consultation(*, identifier: UUID | None = None) -> Consultation:
    values = {
        "patient_name": "Ada Lovelace",
        "primary_concern": "Persistent knee pain",
        "recommended_procedure": "Previous projection",
        "status": ConsultationStatus.PENDING,
    }
    if identifier is not None:
        values["id"] = identifier
    return Consultation(**values)


def _persist_consultation(factory: sessionmaker[Session]) -> Consultation:
    consultation = _new_consultation()
    with factory.begin() as session:
        session.add(consultation)
    return consultation


def test_get_summary_returns_none_when_absent(database) -> None:
    consultation = _persist_consultation(database)
    with database() as session:
        assert SummaryRepository(session).get_summary(consultation.id) is None


def test_complete_and_fresh_retrieval_preserve_ids_and_order(database) -> None:
    consultation = _persist_consultation(database)
    with database() as session:
        attached = session.get(Consultation, consultation.id)
        assert attached is not None
        result = SummaryRepository(session).complete_consultation(
            attached,
            patient_summary="The patient described persistent knee pain.",
            recommended_treatments=(
                "Physical therapy assessment",
                "Clinician follow-up",
                "Home mobility program",
            ),
            recommendation_rationale="Conservative care fits the conversation.",
        )
        assert result.created is True
        assert isinstance(result.aggregate.summary.id, UUID)
        persisted_ids = tuple(item.id for item in result.aggregate.recommendations)

    with database() as fresh_session:
        aggregate = SummaryRepository(fresh_session).get_summary(consultation.id)
        assert aggregate is not None
        assert aggregate.summary.id == result.aggregate.summary.id
        assert aggregate.summary.created_at is not None
        assert aggregate.summary.recommendation_rationale == (
            "Conservative care fits the conversation."
        )
        assert [item.position for item in aggregate.recommendations] == [1, 2, 3]
        assert [item.treatment for item in aggregate.recommendations] == [
            "Physical therapy assessment",
            "Clinician follow-up",
            "Home mobility program",
        ]
        assert tuple(item.id for item in aggregate.recommendations) == persisted_ids
        stored_consultation = fresh_session.get(Consultation, consultation.id)
        assert stored_consultation is not None
        assert stored_consultation.status is ConsultationStatus.COMPLETED
        assert stored_consultation.recommended_procedure == (
            "Physical therapy assessment"
        )


@pytest.mark.parametrize(
    ("treatments", "rationale"),
    [
        ((), None),
        (("Valid treatment", "  "), None),
        (("Valid treatment",), "  "),
    ],
)
def test_completion_failure_rolls_back_entire_aggregate(
    database, treatments, rationale
) -> None:
    consultation = _persist_consultation(database)
    with database() as session:
        attached = session.get(Consultation, consultation.id)
        assert attached is not None
        with pytest.raises((IndexError, IntegrityError)):
            SummaryRepository(session).complete_consultation(
                attached,
                patient_summary="Valid summary",
                recommended_treatments=treatments,
                recommendation_rationale=rationale,
            )
        assert session.scalar(select(func.count(ConsultationSummary.id))) == 0
        assert session.scalar(select(func.count(ConsultationRecommendation.id))) == 0
        reloaded = session.get(Consultation, consultation.id)
        assert reloaded is not None
        assert reloaded.status is ConsultationStatus.PENDING
        assert reloaded.recommended_procedure == "Previous projection"


def test_one_summary_constraint_is_recovered_as_existing(database) -> None:
    consultation = _persist_consultation(database)
    with database() as first_session:
        attached = first_session.get(Consultation, consultation.id)
        assert attached is not None
        winner = SummaryRepository(first_session).complete_consultation(
            attached,
            patient_summary="Winner summary",
            recommended_treatments=("Winner treatment",),
        )

    with database() as losing_session:
        attached = losing_session.get(Consultation, consultation.id)
        assert attached is not None
        recovered = SummaryRepository(losing_session).complete_consultation(
            attached,
            patient_summary="Losing summary",
            recommended_treatments=("Losing treatment",),
        )
        assert recovered.created is False
        assert recovered.aggregate.summary.id == winner.aggregate.summary.id
        assert [item.id for item in recovered.aggregate.recommendations] == [
            item.id for item in winner.aggregate.recommendations
        ]


def test_controlled_concurrent_creators_both_observe_one_winner(database) -> None:
    consultation = _persist_consultation(database)
    barrier = Barrier(2)

    def complete(label: str):
        with database() as session:
            attached = session.get(Consultation, consultation.id)
            assert attached is not None
            repository = SummaryRepository(session)
            assert repository.get_summary(consultation.id) is None
            barrier.wait(timeout=10)
            return repository.complete_consultation(
                attached,
                patient_summary=f"{label} summary",
                recommended_treatments=(f"{label} first", f"{label} second"),
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(complete, ("A", "B")))

    assert sorted(result.created for result in results) == [False, True]
    assert results[0].aggregate.summary.id == results[1].aggregate.summary.id
    assert [item.id for item in results[0].aggregate.recommendations] == [
        item.id for item in results[1].aggregate.recommendations
    ]
    with database() as session:
        assert session.scalar(select(func.count(ConsultationSummary.id))) == 1
        assert session.scalar(select(func.count(ConsultationRecommendation.id))) == 2


def test_unrelated_integrity_error_is_not_treated_as_race(database) -> None:
    consultation = _persist_consultation(database)
    with database() as session:
        attached = session.get(Consultation, consultation.id)
        assert attached is not None
        with pytest.raises(IntegrityError) as caught:
            SummaryRepository(session).complete_consultation(
                attached,
                patient_summary="  ",
                recommended_treatments=("Valid treatment",),
            )
        assert caught.value.orig.diag.constraint_name == (
            "ck_consultation_summaries_patient_summary_nonblank"
        )
        assert SummaryRepository(session).get_summary(consultation.id) is None


def test_restart_creation_persists_only_fresh_consultation(database) -> None:
    source = _persist_consultation(database)
    restart = Consultation(
        patient_name=source.patient_name,
        primary_concern=source.primary_concern,
        recommended_procedure="",
        status=ConsultationStatus.PENDING,
    )
    with database() as session:
        persisted = ConsultationRepository(session).create_consultation(restart)
        assert persisted is restart
        restart_id = persisted.id

    with database() as fresh_session:
        stored = fresh_session.get(Consultation, restart_id)
        assert stored is not None
        assert stored.id != source.id
        assert stored.recommended_procedure == ""
        assert stored.status is ConsultationStatus.PENDING
        assert fresh_session.scalar(select(func.count(Consultation.id))) == 2


def test_restart_insert_failure_rolls_back_and_session_remains_usable(database) -> None:
    source = _persist_consultation(database)
    duplicate = _new_consultation(identifier=source.id)
    with database() as session:
        repository = ConsultationRepository(session)
        with pytest.raises(IntegrityError):
            repository.create_consultation(duplicate)
        created = repository.create_consultation(_new_consultation())
        assert created.id != source.id

    with database() as fresh_session:
        assert fresh_session.scalar(select(func.count(Consultation.id))) == 2
