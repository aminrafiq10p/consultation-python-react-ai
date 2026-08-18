"""CR-004 consultation application service coverage."""

from __future__ import annotations

from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.application.consultation_service import (
    ConsultationApplicationService,
    InvalidConsultationCreationError,
    ConsultationNotFoundError,
)
from app.infrastructure.consultation_models import (
    Consultation,
    ConsultationStatus,
)
from app.repositories.consultation_repository import ConsultationRepository


def test_list_consultations_delegates_filters_to_repository() -> None:
    repository = Mock(spec=ConsultationRepository)
    expected = [
        Mock(spec=Consultation),
        Mock(spec=Consultation),
    ]

    repository.get_consultations.return_value = expected

    service = ConsultationApplicationService(repository)

    result = service.list_consultations(
        search="  knee  ",
        status=ConsultationStatus.PENDING,
    )

    assert result == expected

    repository.get_consultations.assert_called_once_with(
        search="  knee  ",
        status=ConsultationStatus.PENDING,
    )


def test_search_criteria_are_not_normalized_by_application_service() -> None:
    repository = Mock(spec=ConsultationRepository)

    repository.get_consultations.return_value = []

    service = ConsultationApplicationService(repository)

    service.list_consultations(search="   ")

    repository.get_consultations.assert_called_once_with(
        search="   ",
        status=None,
    )


def test_list_consultations_without_filters() -> None:
    repository = Mock(spec=ConsultationRepository)

    repository.get_consultations.return_value = []

    service = ConsultationApplicationService(repository)

    result = service.list_consultations()

    assert result == []

    repository.get_consultations.assert_called_once_with(
        search=None,
        status=None,
    )


def test_get_consultation_delegates_to_repository() -> None:
    repository = Mock(spec=ConsultationRepository)
    consultation_id = uuid4()
    expected = Mock(spec=Consultation)

    repository.get_consultation_by_id.return_value = expected

    service = ConsultationApplicationService(repository)

    result = service.get_consultation(consultation_id)

    assert result is expected

    repository.get_consultation_by_id.assert_called_once_with(
        consultation_id,
    )


def test_get_consultation_raises_not_found_when_repository_returns_none() -> None:
    repository = Mock(spec=ConsultationRepository)
    consultation_id = uuid4()

    repository.get_consultation_by_id.return_value = None

    service = ConsultationApplicationService(repository)

    with pytest.raises(ConsultationNotFoundError):
        service.get_consultation(consultation_id)

    repository.get_consultation_by_id.assert_called_once_with(
        consultation_id,
    )


def test_create_consultation_constructs_server_controlled_pending_record() -> None:
    repository = Mock(spec=ConsultationRepository)
    confirmed = Consultation(
        patient_name="Amina Khan",
        primary_concern="Persistent knee pain",
        recommended_procedure="",
        status=ConsultationStatus.PENDING,
    )
    repository.create_consultation.return_value = confirmed
    service = ConsultationApplicationService(
        repository,
        message_repository=Mock(),
        ai_service=Mock(),
        summary_repository=Mock(),
        appointment_repository=Mock(),
    )

    result = service.create_consultation(
        "  Amina Khan  ",
        "  Persistent knee pain  ",
    )

    assert result is confirmed
    repository.create_consultation.assert_called_once()
    created = repository.create_consultation.call_args.args[0]
    assert {
        "id",
        "patient_name",
        "primary_concern",
        "recommended_procedure",
        "status",
    } == set(created.__dict__) - {"_sa_instance_state"}
    assert created.patient_name == "Amina Khan"
    assert created.primary_concern == "Persistent knee pain"
    assert created.recommended_procedure == ""
    assert created.status is ConsultationStatus.PENDING
    assert created.id is not None
    assert created.id != confirmed.id


def test_create_consultation_uses_fresh_unique_uuids_and_returns_confirmed_records() -> None:
    repository = Mock(spec=ConsultationRepository)
    repository.create_consultation.side_effect = lambda record: record
    service = ConsultationApplicationService(repository)

    first = service.create_consultation("Ada", "Concern one")
    second = service.create_consultation("Grace", "Concern two")

    assert first.id is not None and second.id is not None
    assert first.id != second.id
    assert repository.create_consultation.call_count == 2


@pytest.mark.parametrize(
    ("patient_name", "primary_concern"),
    [
        ("", "Concern"),
        ("   ", "Concern"),
        ("Patient", ""),
        ("Patient", "\t\n"),
        ("x" * 201, "Concern"),
        ("Patient", "x" * 4_001),
        (123, "Concern"),
        ("Patient", False),
    ],
)
def test_create_consultation_rejects_invalid_inputs_without_side_effects(
    patient_name: object, primary_concern: object
) -> None:
    repository = Mock(spec=ConsultationRepository)
    messages = Mock()
    ai = Mock()
    summaries = Mock()
    appointments = Mock()
    service = ConsultationApplicationService(
        repository,
        message_repository=messages,
        ai_service=ai,
        summary_repository=summaries,
        appointment_repository=appointments,
    )

    with pytest.raises(InvalidConsultationCreationError):
        service.create_consultation(patient_name, primary_concern)  # type: ignore[arg-type]

    repository.create_consultation.assert_not_called()
    messages.assert_not_called()
    ai.assert_not_called()
    summaries.assert_not_called()
    appointments.assert_not_called()
    
