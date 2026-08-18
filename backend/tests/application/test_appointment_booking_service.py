"""AB-004 deterministic appointment-booking application coverage."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from app.ai import AIService
from app.application.consultation_service import (
    AppointmentAlreadyExistsError,
    ConsultationApplicationService,
    ConsultationNotBookableError,
    ConsultationNotFoundError,
    InvalidAppointmentBookingError,
    RecommendationNotBookableError,
    RecommendationNotFoundError,
)
from app.infrastructure.consultation_models import ConsultationStatus
from app.repositories.appointment_repository import (
    AppointmentAggregate,
    AppointmentCreation,
    AppointmentRepository,
)
from app.repositories.consultation_repository import ConsultationRepository

NOW = datetime(2026, 8, 18, 12, 0, tzinfo=timezone.utc)


def booking_service(
    *,
    status: ConsultationStatus = ConsultationStatus.COMPLETED,
) -> tuple[ConsultationApplicationService, Mock, SimpleNamespace, SimpleNamespace]:
    records = Mock(spec=ConsultationRepository)
    appointments = Mock(spec=AppointmentRepository)
    consultation = SimpleNamespace(
        id=uuid4(),
        status=status,
        messages=["unchanged"],
        recommended_procedure="Clinical assessment",
    )
    summary = SimpleNamespace(id=uuid4(), consultation_id=consultation.id)
    recommendation = SimpleNamespace(
        id=uuid4(), summary_id=summary.id, treatment="Physiotherapy", position=0
    )
    appointments.lock_consultation.return_value = consultation
    appointments.get_appointment.return_value = None
    appointments.get_summary.return_value = summary
    appointments.get_recommendation.return_value = recommendation
    aggregate = AppointmentAggregate(
        appointment=SimpleNamespace(
            id=uuid4(),
            consultation_id=consultation.id,
            recommendation_id=recommendation.id,
            scheduled_at=NOW + timedelta(days=1),
            location="Downtown Clinic",
            created_at=NOW,
        ),
        recommendation=recommendation,
    )
    appointments.create_appointment.return_value = AppointmentCreation(
        aggregate=aggregate, created=True
    )
    service = ConsultationApplicationService(
        records,
        ai_service=Mock(spec=AIService),
        appointment_repository=appointments,
        clock=lambda: NOW,
    )
    return service, appointments, consultation, recommendation


def book(
    service: ConsultationApplicationService,
    consultation_id: UUID,
    recommendation_id: UUID,
    *,
    scheduled_at: datetime = NOW + timedelta(hours=1),
    location: str = "Downtown Clinic",
) -> AppointmentAggregate:
    return service.book_appointment(
        consultation_id, recommendation_id, scheduled_at, location
    )


@pytest.mark.parametrize(
    "scheduled_at",
    [NOW.replace(tzinfo=None), NOW, NOW - timedelta(microseconds=1)],
)
def test_invalid_time_fails_before_repository_transaction(
    scheduled_at: datetime,
) -> None:
    service, appointments, consultation, recommendation = booking_service()

    with pytest.raises(InvalidAppointmentBookingError):
        book(
            service,
            consultation.id,
            recommendation.id,
            scheduled_at=scheduled_at,
        )

    appointments.lock_consultation.assert_not_called()
    appointments.create_appointment.assert_not_called()


@pytest.mark.parametrize("location", ["", " \t\n", "x" * 201])
def test_invalid_location_fails_before_repository_transaction(location: str) -> None:
    service, appointments, consultation, recommendation = booking_service()

    with pytest.raises(InvalidAppointmentBookingError):
        book(service, consultation.id, recommendation.id, location=location)

    appointments.lock_consultation.assert_not_called()
    appointments.create_appointment.assert_not_called()


def test_invalid_identifier_fails_before_clock_or_repository() -> None:
    service, appointments, consultation, recommendation = booking_service()

    with pytest.raises(InvalidAppointmentBookingError):
        service.book_appointment("not-a-uuid", recommendation.id, NOW, "Clinic")  # type: ignore[arg-type]

    appointments.lock_consultation.assert_not_called()


def test_future_equivalent_offset_and_normalized_location_are_forwarded() -> None:
    service, appointments, consultation, recommendation = booking_service()
    offset_time = datetime(2026, 8, 18, 18, 0, tzinfo=timezone(timedelta(hours=5)))

    result = book(
        service,
        consultation.id,
        recommendation.id,
        scheduled_at=offset_time,
        location=f"  {'é' * 200}  ",
    )

    appointments.create_appointment.assert_called_once_with(
        consultation,
        recommendation,
        scheduled_at=datetime(2026, 8, 18, 13, 0, tzinfo=timezone.utc),
        location="é" * 200,
    )
    assert result is appointments.create_appointment.return_value.aggregate
    assert result.recommendation is recommendation


def test_clock_is_captured_once_per_booking_attempt() -> None:
    service, _, consultation, recommendation = booking_service()
    clock = Mock(return_value=NOW)
    service._clock = clock

    book(service, consultation.id, recommendation.id)

    clock.assert_called_once_with()


@pytest.mark.parametrize(
    ("configure", "expected", "expected_calls"),
    [
        (lambda repo, record, rec: setattr(repo, "lock_consultation", Mock(return_value=None)), ConsultationNotFoundError, ()),
        (lambda repo, record, rec: setattr(repo, "get_appointment", Mock(return_value=object())), AppointmentAlreadyExistsError, ("get_appointment",)),
        (lambda repo, record, rec: setattr(record, "status", ConsultationStatus.BOOKED), AppointmentAlreadyExistsError, ("get_appointment",)),
        (lambda repo, record, rec: setattr(record, "status", ConsultationStatus.PENDING), ConsultationNotBookableError, ("get_appointment",)),
        (lambda repo, record, rec: setattr(repo, "get_summary", Mock(return_value=None)), RecommendationNotBookableError, ("get_appointment", "get_summary")),
        (lambda repo, record, rec: setattr(repo, "get_recommendation", Mock(return_value=None)), RecommendationNotFoundError, ("get_appointment", "get_summary", "get_recommendation")),
        (lambda repo, record, rec: setattr(rec, "summary_id", uuid4()), RecommendationNotBookableError, ("get_appointment", "get_summary", "get_recommendation")),
    ],
)
def test_locked_business_outcomes_abort_without_creating(
    configure: object, expected: type[Exception], expected_calls: tuple[str, ...]
) -> None:
    service, appointments, consultation, recommendation = booking_service()
    configure(appointments, consultation, recommendation)  # type: ignore[operator]

    with pytest.raises(expected):
        book(service, consultation.id, recommendation.id)

    appointments.abort.assert_called_once_with()
    appointments.create_appointment.assert_not_called()
    for call in expected_calls:
        getattr(appointments, call).assert_called_once()


def test_existing_appointment_precedes_booked_status_and_other_conflicts() -> None:
    service, appointments, consultation, recommendation = booking_service(
        status=ConsultationStatus.BOOKED
    )
    appointments.get_appointment.return_value = object()
    appointments.get_summary.return_value = None
    appointments.get_recommendation.return_value = None

    with pytest.raises(AppointmentAlreadyExistsError):
        book(service, consultation.id, recommendation.id)

    appointments.get_summary.assert_not_called()
    appointments.get_recommendation.assert_not_called()


def test_matching_treatment_does_not_bypass_recommendation_ownership() -> None:
    service, appointments, consultation, recommendation = booking_service()
    recommendation.summary_id = uuid4()
    recommendation.treatment = "Clinical assessment"

    with pytest.raises(RecommendationNotBookableError):
        book(service, consultation.id, recommendation.id)

    appointments.create_appointment.assert_not_called()


def test_duplicate_race_aborts_and_becomes_already_exists() -> None:
    service, appointments, consultation, recommendation = booking_service()
    appointments.create_appointment.return_value = AppointmentCreation(
        aggregate=appointments.create_appointment.return_value.aggregate,
        created=False,
    )

    with pytest.raises(AppointmentAlreadyExistsError):
        book(service, consultation.id, recommendation.id)

    appointments.abort.assert_called_once_with()


def test_unexpected_repository_failure_is_not_translated() -> None:
    service, appointments, consultation, recommendation = booking_service()
    appointments.create_appointment.side_effect = OSError("storage unavailable")

    with pytest.raises(OSError, match="storage unavailable"):
        book(service, consultation.id, recommendation.id)

    appointments.abort.assert_not_called()


def test_success_does_not_invoke_ai_or_mutate_source_data() -> None:
    service, _, consultation, recommendation = booking_service()
    original = (
        consultation.status,
        list(consultation.messages),
        consultation.recommended_procedure,
        recommendation.summary_id,
        recommendation.treatment,
        recommendation.position,
    )

    book(service, consultation.id, recommendation.id)

    service._ai_service.generate_response.assert_not_called()
    service._ai_service.generate_summary.assert_not_called()
    assert (
        consultation.status,
        consultation.messages,
        consultation.recommended_procedure,
        recommendation.summary_id,
        recommendation.treatment,
        recommendation.position,
    ) == original
