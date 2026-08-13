"""CR-002 PostgreSQL migration and consultation mapping coverage."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.exc import DataError, IntegrityError

from app.infrastructure.database import create_database_engine, create_session_factory
from app.infrastructure.consultation_models import Consultation, ConsultationStatus


BACKEND_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def migrated_database_url(postgresql_url: str) -> str:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", postgresql_url)
    command.upgrade(config, "head")
    return postgresql_url


def test_migration_stores_and_retrieves_all_approved_consultation_values(
    migrated_database_url: str,
) -> None:
    engine = create_database_engine(migrated_database_url)
    session_factory = create_session_factory(engine)
    consultations = [
        Consultation(
            patient_name="Ada Lovelace",
            primary_concern="Persistent knee pain",
            recommended_procedure="Physical therapy assessment",
            status=ConsultationStatus.PENDING,
        ),
        Consultation(
            patient_name="Grace Hopper",
            primary_concern="Migraine review",
            recommended_procedure="Neurology consultation",
            status=ConsultationStatus.BOOKED,
        ),
        Consultation(
            patient_name="Katherine Johnson",
            primary_concern="Shoulder stiffness",
            recommended_procedure="Mobility program",
            status=ConsultationStatus.COMPLETED,
        ),
    ]

    with session_factory.begin() as session:
        session.add_all(consultations)

    with session_factory() as session:
        stored = {
            consultation.id: session.get(Consultation, consultation.id)
            for consultation in consultations
        }

    assert set(inspect(engine).get_table_names()) == {"alembic_version", "consultations"}
    assert all(record is not None for record in stored.values())
    assert stored[consultations[0].id].patient_name == "Ada Lovelace"
    assert stored[consultations[0].id].primary_concern == "Persistent knee pain"
    assert stored[consultations[0].id].recommended_procedure == "Physical therapy assessment"
    assert stored[consultations[0].id].status is ConsultationStatus.PENDING
    assert stored[consultations[1].id].status is ConsultationStatus.BOOKED
    assert stored[consultations[2].id].status is ConsultationStatus.COMPLETED
    engine.dispose()


def test_migration_enforces_required_columns_and_approved_status_values(
    migrated_database_url: str,
) -> None:
    engine = create_database_engine(migrated_database_url)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        with pytest.raises(IntegrityError):
            session.execute(
                text("INSERT INTO consultations (id) VALUES (:id)"),
                {"id": uuid4()},
            )
            session.commit()
        session.rollback()

        with pytest.raises(DataError):
            session.execute(
                text(
                    """
                    INSERT INTO consultations (
                        id, patient_name, primary_concern, recommended_procedure, status
                    ) VALUES (:id, :patient_name, :primary_concern, :recommended_procedure, :status)
                    """
                ),
                {
                    "id": uuid4(),
                    "patient_name": "Lin Lanying",
                    "primary_concern": "Back pain",
                    "recommended_procedure": "Clinical review",
                    "status": "INVALID",
                },
            )
            session.commit()
        session.rollback()

    engine.dispose()
