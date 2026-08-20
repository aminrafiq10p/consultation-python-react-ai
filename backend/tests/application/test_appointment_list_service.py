"""AP-003 appointment-list application operation coverage."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from app.ai import AIService
from app.application.consultation_service import ConsultationApplicationService
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.consultation_repository import ConsultationRepository


def test_list_appointments_delegates_once_and_preserves_repository_identity() -> None:
    consultation_repository = Mock(spec=ConsultationRepository)
    appointment_repository = Mock(spec=AppointmentRepository)
    expected = [Mock()]
    appointment_repository.list_appointments.return_value = expected

    service = ConsultationApplicationService(
        consultation_repository,
        appointment_repository=appointment_repository,
    )

    result = service.list_appointments()

    assert result is expected
    appointment_repository.list_appointments.assert_called_once_with()


def test_list_appointments_requires_the_existing_appointment_dependency() -> None:
    service = ConsultationApplicationService(Mock(spec=ConsultationRepository))

    with pytest.raises(RuntimeError, match="Appointment repository is not configured"):
        service.list_appointments()


def test_list_appointments_propagates_repository_failure_without_translation() -> None:
    consultation_repository = Mock(spec=ConsultationRepository)
    appointment_repository = Mock(spec=AppointmentRepository)
    failure = OSError("storage unavailable")
    appointment_repository.list_appointments.side_effect = failure
    service = ConsultationApplicationService(
        consultation_repository,
        appointment_repository=appointment_repository,
    )

    with pytest.raises(OSError, match="storage unavailable") as raised:
        service.list_appointments()

    assert raised.value is failure
    appointment_repository.list_appointments.assert_called_once_with()


def test_list_appointments_does_not_invoke_booking_mutation_or_ai() -> None:
    consultation_repository = Mock(spec=ConsultationRepository)
    appointment_repository = Mock(spec=AppointmentRepository)
    ai_service = Mock(spec=AIService)
    appointment_repository.list_appointments.return_value = []
    service = ConsultationApplicationService(
        consultation_repository,
        ai_service=ai_service,
        appointment_repository=appointment_repository,
    )

    assert service.list_appointments() == []

    appointment_repository.list_appointments.assert_called_once_with()
    appointment_repository.lock_consultation.assert_not_called()
    appointment_repository.get_appointment.assert_not_called()
    appointment_repository.get_summary.assert_not_called()
    appointment_repository.get_recommendation.assert_not_called()
    appointment_repository.get_owned_recommendation.assert_not_called()
    appointment_repository.create_appointment.assert_not_called()
    appointment_repository.abort.assert_not_called()
    ai_service.generate_response.assert_not_called()
    ai_service.generate_summary.assert_not_called()
