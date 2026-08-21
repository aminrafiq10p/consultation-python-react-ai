from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.ai import AIResult, AIService
from app.application.booking_handoff import BookingHandoffAction, project_message_payload
from app.application.booking_intent import BookingIntent
from app.application.consultation_service import (
    AIGenerationError,
    ConsultationApplicationService,
    ConsultationConversationClosedError,
)
from app.infrastructure.consultation_models import (
    Consultation,
    ConsultationStatus,
    Message,
    MessageRole,
)
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.summary_repository import SummaryRepository


def _consultation(status: ConsultationStatus = ConsultationStatus.PENDING) -> Consultation:
    return Consultation(
        id=uuid4(),
        patient_name="Ada Lovelace",
        primary_concern="Persistent knee pain",
        recommended_procedure="Clinical assessment",
        status=status,
    )


def _message(consultation_id, role, content) -> Message:
    return Message(
        id=uuid4(),
        consultation_id=consultation_id,
        role=role,
        content=content,
        created_at=datetime.now(UTC),
    )


def _service(record, history, *, summary=None, appointment=None, ai_result=None):
    consultations = Mock(spec=ConsultationRepository)
    consultations.get_consultation_by_id.return_value = record
    messages = Mock(spec=MessageRepository)
    persisted = []

    def persist(item):
        persisted.append(item)
        return item

    messages.persist_message.side_effect = persist
    messages.list_messages.side_effect = lambda _: [*history, *persisted[:1]]
    ai = Mock(spec=AIService)
    ai.generate_response.return_value = ai_result or AIResult("I can help with that.")
    summaries = Mock(spec=SummaryRepository)
    summaries.get_summary.return_value = summary
    appointments = Mock(spec=AppointmentRepository)
    appointments.get_appointment.return_value = appointment
    return (
        ConsultationApplicationService(
            consultations,
            messages,
            ai,
            summaries,
            appointments,
        ),
        messages,
        appointments,
        persisted,
    )


def test_ordinary_message_has_no_handoff_or_state_read():
    record = _consultation()
    service, messages, appointments, persisted = _service(record, [])

    service.submit_message(record.id, "Tell me more about my symptoms")

    assert persisted[-1].structured_payload is None
    appointments.get_appointment.assert_not_called()


def test_reloading_persisted_handoff_does_not_call_ai_or_mutate_state():
    record = _consultation()
    handoff = {
        "_application_handoff_action": BookingHandoffAction.GENERATE_SUMMARY.value,
        "_application_handoff_consultation_id": str(record.id),
    }
    persisted = Message(
        consultation_id=record.id,
        role=MessageRole.ASSISTANT,
        content="Use the existing summary workflow for the next step.",
        structured_payload={"provider": "informational", **handoff},
    )
    service, messages, appointments, _ = _service(record, [persisted])

    reloaded = service.get_messages(record.id)

    assert reloaded == [persisted]
    assert service._ai_service.generate_response.call_count == 0
    assert service._ai_service.generate_summary.call_count == 0
    messages.persist_message.assert_not_called()
    appointments.get_appointment.assert_not_called()
    assert record.status is ConsultationStatus.PENDING


@pytest.mark.parametrize("status", [ConsultationStatus.COMPLETED, ConsultationStatus.BOOKED])
def test_closed_state_reload_does_not_reopen_or_submit_messages(status):
    record = _consultation(status)
    service, messages, _, _ = _service(record, [])

    reloaded = service.get_messages(record.id)

    assert reloaded == []
    with pytest.raises(ConsultationConversationClosedError):
        service.submit_message(record.id, "Book an appointment")
    messages.persist_message.assert_not_called()
    assert record.status is status


@pytest.mark.parametrize(
    ("history", "expected"),
    [
        ([_message(uuid4(), MessageRole.USER, "Earlier")], BookingHandoffAction.CONTINUE_CONSULTATION),
        (
            [
                _message(uuid4(), MessageRole.USER, "Earlier"),
                _message(uuid4(), MessageRole.ASSISTANT, "Follow-up"),
            ],
            BookingHandoffAction.GENERATE_SUMMARY,
        ),
    ],
)
def test_pending_handoff_uses_prior_persisted_summary_eligibility(history, expected):
    record = _consultation()
    history = [
        Message(
            id=item.id,
            consultation_id=record.id,
            role=item.role,
            content=item.content,
            created_at=item.created_at,
        )
        for item in history
    ]
    service, _, _, persisted = _service(record, history)

    service.submit_message(record.id, "Please book an appointment")

    payload, handoff = project_message_payload(
        persisted[-1].structured_payload,
        MessageRole.ASSISTANT,
        record.id,
    )
    assert payload is None
    assert handoff is not None
    assert handoff.action is expected


def test_provider_action_like_payload_cannot_override_authoritative_action():
    record = _consultation()
    service, _, _, persisted = _service(
        record,
        [],
        ai_result=AIResult(
            "I can help.",
            {"action": "VIEW_APPOINTMENTS", "_application_handoff_action": "VIEW_APPOINTMENTS"},
        ),
    )

    service.submit_message(record.id, "Schedule an appointment")

    _, handoff = project_message_payload(
        persisted[-1].structured_payload,
        MessageRole.ASSISTANT,
        record.id,
    )
    assert handoff is not None
    assert handoff.action is BookingHandoffAction.CONTINUE_CONSULTATION
    assert persisted[-1].structured_payload["action"] == "VIEW_APPOINTMENTS"


def test_state_lookup_failure_keeps_assistant_exchange_without_handoff():
    record = _consultation()
    service, _, appointments, persisted = _service(record, [])
    appointments.get_appointment.side_effect = RuntimeError("read failed")

    exchange = service.submit_message(record.id, "Make an appointment")

    assert exchange.assistant_message.structured_payload is None


def test_handoff_does_not_write_appointment_or_mutate_consultation():
    record = _consultation()
    service, _, appointments, persisted = _service(record, [])

    service.submit_message(record.id, "I want to make an appointment")

    assert appointments.create_appointment.call_count == 0
    assert record.status is ConsultationStatus.PENDING
    assert len(persisted) == 2


@pytest.mark.parametrize(
    ("status", "summary", "appointment", "expected"),
    [
        (
            ConsultationStatus.COMPLETED,
            SimpleNamespace(
                summary=SimpleNamespace(consultation_id=None),
                recommendations=(object(),),
            ),
            None,
            BookingHandoffAction.VIEW_SUMMARY,
        ),
        (
            ConsultationStatus.BOOKED,
            None,
            object(),
            BookingHandoffAction.VIEW_APPOINTMENTS,
        ),
    ],
)
def test_closed_lifecycle_mapping_is_authoritative(status, summary, appointment, expected):
    record = _consultation(status)
    if summary is not None:
        summary.summary.consultation_id = record.id
    service, _, _, _ = _service(record, [], summary=summary, appointment=appointment)

    handoff = service._evaluate_booking_handoff(
        record,
        [],
        BookingIntent.BOOKING_REQUEST,
    )

    assert handoff is not None
    assert handoff.action is expected


def test_provider_failure_preserves_existing_user_recovery_semantics():
    record = _consultation()
    service, messages, _, persisted = _service(record, [])
    service._ai_service.generate_response.side_effect = RuntimeError("provider failed")

    with pytest.raises(AIGenerationError) as caught:
        service.submit_message(record.id, "Book an appointment")

    assert caught.value.user_message is persisted[0]
    assert len(persisted) == 1
    messages.persist_message.assert_called_once()


@pytest.mark.parametrize("status", [ConsultationStatus.COMPLETED, ConsultationStatus.BOOKED])
def test_non_pending_submit_remains_closed(status):
    record = _consultation(status)
    service, messages, _, _ = _service(record, [])

    with pytest.raises(ConsultationConversationClosedError):
        service.submit_message(record.id, "Book an appointment")

    messages.persist_message.assert_not_called()
