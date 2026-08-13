"""CR-004 consultation application service coverage."""

from __future__ import annotations

from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.application.consultation_service import (
    ConsultationApplicationService,
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
    
