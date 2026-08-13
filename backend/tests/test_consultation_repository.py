"""CR-003 consultation repository coverage."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from app.infrastructure.consultation_models import (
    Consultation,
    ConsultationStatus,
    Message,
)
from app.repositories.consultation_repository import ConsultationRepository
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def migrated_database_url(postgresql_url: str) -> str:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option(
        "script_location",
        str(BACKEND_ROOT / "migrations"),
    )
    config.set_main_option("sqlalchemy.url", postgresql_url)

    command.upgrade(config, "head")

    return postgresql_url


@pytest.fixture(scope="module")
def database_engine(migrated_database_url: str) -> Engine:
    engine = create_engine(
        migrated_database_url,
        pool_pre_ping=True,
    )

    yield engine

    engine.dispose()


@pytest.fixture
def db_session(database_engine: Engine):
    session_factory = sessionmaker(
        bind=database_engine,
        expire_on_commit=False,
    )

    with session_factory() as session:
        # Messages reference consultations, so clean the child table first.
        session.query(Message).delete()
        session.query(Consultation).delete()
        session.commit()

        yield session

        # Ensure test data does not leak into the next test.
        session.rollback()
        session.query(Message).delete()
        session.query(Consultation).delete()
        session.commit()


def seed_consultations(session: Session) -> list[Consultation]:
    consultations = [
        Consultation(
            patient_name="Alice Smith",
            primary_concern="Persistent knee pain",
            recommended_procedure="Physical therapy assessment",
            status=ConsultationStatus.PENDING,
        ),
        Consultation(
            patient_name="Bob Jones",
            primary_concern="Migraine review",
            recommended_procedure="Neurology consultation",
            status=ConsultationStatus.BOOKED,
        ),
        Consultation(
            patient_name="Carol Williams",
            primary_concern="Shoulder stiffness",
            recommended_procedure="Mobility program",
            status=ConsultationStatus.COMPLETED,
        ),
        Consultation(
            patient_name="David Brown",
            primary_concern="Persistent knee pain",
            recommended_procedure="Orthopedic consultation",
            status=ConsultationStatus.PENDING,
        ),
    ]

    session.add_all(consultations)
    session.commit()

    return consultations


def test_get_consultations_returns_persisted_records(
    db_session: Session,
) -> None:
    consultations = seed_consultations(db_session)

    repository = ConsultationRepository(db_session)

    results = repository.get_consultations()

    assert {item.id for item in results} == {
        item.id for item in consultations
    }


def test_search_matches_patient_name(
    db_session: Session,
) -> None:
    seed_consultations(db_session)

    repository = ConsultationRepository(db_session)

    results = repository.get_consultations(search="alice")

    assert len(results) == 1
    assert results[0].patient_name == "Alice Smith"


def test_search_is_case_insensitive(
    db_session: Session,
) -> None:
    seed_consultations(db_session)

    repository = ConsultationRepository(db_session)

    results = repository.get_consultations(search="KNEE")

    assert len(results) == 2


def test_search_matches_recommended_procedure(
    db_session: Session,
) -> None:
    seed_consultations(db_session)

    repository = ConsultationRepository(db_session)

    results = repository.get_consultations(search="neurology")

    assert len(results) == 1
    assert results[0].patient_name == "Bob Jones"


def test_status_filtering(
    db_session: Session,
) -> None:
    seed_consultations(db_session)

    repository = ConsultationRepository(db_session)

    results = repository.get_consultations(
        status=ConsultationStatus.PENDING,
    )

    assert len(results) == 2
    assert all(
        item.status is ConsultationStatus.PENDING
        for item in results
    )


def test_combined_search_and_status_filtering(
    db_session: Session,
) -> None:
    seed_consultations(db_session)

    repository = ConsultationRepository(db_session)

    results = repository.get_consultations(
        search="knee",
        status=ConsultationStatus.PENDING,
    )

    assert len(results) == 2
    assert all(
        item.status is ConsultationStatus.PENDING
        for item in results
    )


def test_get_consultation_by_id(
    db_session: Session,
) -> None:
    consultations = seed_consultations(db_session)

    repository = ConsultationRepository(db_session)

    result = repository.get_consultation_by_id(
        consultations[0].id,
    )

    assert result is not None
    assert result.id == consultations[0].id
    assert result.patient_name == "Alice Smith"


def test_get_consultation_by_id_returns_none_when_missing(
    db_session: Session,
) -> None:
    seed_consultations(db_session)

    repository = ConsultationRepository(db_session)

    result = repository.get_consultation_by_id(uuid4())

    assert result is None
