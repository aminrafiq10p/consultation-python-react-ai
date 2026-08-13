"""AI-005 persistent conversation application workflow coverage."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from app.ai import AIResult, AIService
from app.application.consultation_service import (
    AIGenerationError,
    ConsultationApplicationService,
    ConsultationNotFoundError,
    InvalidMessageError,
    MAX_CONTEXT_CHARACTERS,
    MAX_CONTEXT_MESSAGES,
)
from app.infrastructure.consultation_models import (
    Consultation,
    ConsultationStatus,
    Message,
    MessageRole,
)
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.message_repository import MessageRepository


def consultation(consultation_id: UUID | None = None) -> Consultation:
    return Consultation(
        id=consultation_id or uuid4(),
        patient_name="Ada Lovelace",
        primary_concern="Persistent knee pain",
        recommended_procedure="Clinical assessment",
        status=ConsultationStatus.PENDING,
    )


def message(
    consultation_id: UUID,
    role: MessageRole,
    content: str,
    *,
    offset: int = 0,
    payload: dict[str, object] | None = None,
) -> Message:
    return Message(
        id=uuid4(),
        consultation_id=consultation_id,
        role=role,
        content=content,
        structured_payload=payload,
        created_at=datetime(2026, 8, 13, tzinfo=UTC) + timedelta(seconds=offset),
    )


def service_with(
    record: Consultation | None,
    *,
    history: list[Message] | None = None,
    ai_result: object | None = None,
) -> tuple[ConsultationApplicationService, Mock, Mock, Mock]:
    consultation_repository = Mock(spec=ConsultationRepository)
    consultation_repository.get_consultation_by_id.return_value = record
    message_repository = Mock(spec=MessageRepository)
    message_repository.list_messages.return_value = history or []
    message_repository.persist_message.side_effect = lambda item: item
    ai_service = Mock(spec=AIService)
    ai_service.generate_response.return_value = ai_result or AIResult("Helpful response")
    return (
        ConsultationApplicationService(
            consultation_repository,
            message_repository,
            ai_service,
        ),
        consultation_repository,
        message_repository,
        ai_service,
    )


def test_get_messages_checks_consultation_and_returns_repository_order() -> None:
    record = consultation()
    history = [
        message(record.id, MessageRole.USER, "First", offset=1),
        message(record.id, MessageRole.ASSISTANT, "Second", offset=2),
    ]
    service, consultation_repository, message_repository, _ = service_with(
        record, history=history
    )

    assert service.get_messages(record.id) == history
    consultation_repository.get_consultation_by_id.assert_called_once_with(record.id)
    message_repository.list_messages.assert_called_once_with(record.id)


def test_get_messages_returns_empty_history_for_existing_consultation() -> None:
    record = consultation()
    service, _, _, _ = service_with(record)

    assert service.get_messages(record.id) == []


def test_get_messages_missing_consultation_does_not_load_history() -> None:
    consultation_id = uuid4()
    service, _, message_repository, _ = service_with(None)

    with pytest.raises(ConsultationNotFoundError):
        service.get_messages(consultation_id)

    message_repository.list_messages.assert_not_called()


@pytest.mark.parametrize("content", ["", "   \n\t", "x" * 4_001, 123])
def test_invalid_submission_writes_nothing_and_does_not_call_ai(content: object) -> None:
    record = consultation()
    service, consultation_repository, message_repository, ai_service = service_with(record)

    with pytest.raises(InvalidMessageError):
        service.submit_message(record.id, content)  # type: ignore[arg-type]

    consultation_repository.get_consultation_by_id.assert_not_called()
    message_repository.persist_message.assert_not_called()
    ai_service.generate_response.assert_not_called()


def test_missing_consultation_submission_writes_nothing_and_does_not_call_ai() -> None:
    consultation_id = uuid4()
    service, _, message_repository, ai_service = service_with(None)

    with pytest.raises(ConsultationNotFoundError):
        service.submit_message(consultation_id, "Hello")

    message_repository.persist_message.assert_not_called()
    ai_service.generate_response.assert_not_called()


def test_success_normalizes_and_orders_user_before_ai_before_assistant() -> None:
    record = consultation()
    old = message(record.id, MessageRole.ASSISTANT, "Earlier", offset=1)
    events: list[str] = []
    service, _, message_repository, ai_service = service_with(
        record,
        ai_result=AIResult("  Answer  ", {"topics": ["pain", 2]}),
    )

    def persist(item: Message) -> Message:
        item.id = uuid4()
        item.created_at = datetime.now(UTC)
        events.append(f"persist:{item.role.value}")
        return item

    persisted: list[Message] = []

    def persist_and_track(item: Message) -> Message:
        confirmed = persist(item)
        persisted.append(confirmed)
        return confirmed

    message_repository.persist_message.side_effect = persist_and_track
    message_repository.list_messages.side_effect = lambda _: (
        events.append("reload") or [old, persisted[0]]
    )
    ai_service.generate_response.side_effect = lambda *_: (
        events.append("ai") or AIResult("  Answer  ", {"topics": ["pain", 2]})
    )

    exchange = service.submit_message(record.id, "  My question  ")

    assert events == ["persist:USER", "reload", "ai", "persist:ASSISTANT"]
    assert exchange.user_message is persisted[0]
    assert exchange.assistant_message is persisted[1]
    assert exchange.user_message.content == "My question"
    assert exchange.assistant_message.content == "Answer"
    assert exchange.assistant_message.structured_payload == {"topics": ["pain", 2]}
    context, messages = ai_service.generate_response.call_args.args
    assert context.consultation_id == str(record.id)
    assert context.primary_concern == record.primary_concern
    assert context.display_fields == {
        "patient_name": record.patient_name,
        "recommended_procedure": record.recommended_procedure,
        "status": "PENDING",
    }
    assert [(item.role, item.content) for item in messages] == [
        ("ASSISTANT", "Earlier"),
        ("USER", "My question"),
    ]


def test_context_keeps_newest_twenty_in_chronological_order_without_deleting() -> None:
    record = consultation()
    history = [
        message(record.id, MessageRole.USER, f"message-{index}", offset=index)
        for index in range(25)
    ]
    current = history[-1]
    service, _, message_repository, ai_service = service_with(record, history=history)
    message_repository.persist_message.side_effect = [current, message(record.id, MessageRole.ASSISTANT, "ok")]

    service.submit_message(record.id, current.content)

    sent = ai_service.generate_response.call_args.args[1]
    assert len(sent) == MAX_CONTEXT_MESSAGES
    assert [item.content for item in sent] == [f"message-{index}" for index in range(5, 25)]
    message_repository.list_messages.assert_called_once_with(record.id)
    assert len(history) == 25


def test_context_character_boundary_retains_current_user_and_whole_messages() -> None:
    record = consultation()
    too_old = message(record.id, MessageRole.USER, "z", offset=1)
    at_boundary = message(
        record.id,
        MessageRole.ASSISTANT,
        "a" * (MAX_CONTEXT_CHARACTERS - 4),
        offset=2,
    )
    current = message(record.id, MessageRole.USER, "last", offset=3)
    history = [too_old, at_boundary, current]
    service, _, message_repository, ai_service = service_with(record, history=history)
    message_repository.persist_message.side_effect = [current, message(record.id, MessageRole.ASSISTANT, "ok")]

    service.submit_message(record.id, "last")

    sent = ai_service.generate_response.call_args.args[1]
    assert [item.content for item in sent] == [at_boundary.content, "last"]
    assert sum(len(item.content) for item in sent) == MAX_CONTEXT_CHARACTERS


def test_user_persistence_failure_prevents_reload_and_ai() -> None:
    record = consultation()
    service, _, message_repository, ai_service = service_with(record)
    message_repository.persist_message.side_effect = RuntimeError("database unavailable")

    with pytest.raises(RuntimeError, match="database unavailable"):
        service.submit_message(record.id, "Question")

    message_repository.list_messages.assert_not_called()
    ai_service.generate_response.assert_not_called()


@pytest.mark.parametrize(
    "ai_outcome",
    [RuntimeError("provider detail"), SimpleNamespace(content="   ", structured_payload=None), SimpleNamespace(content="ok", structured_payload={"nested": {"bad": True}})],
)
def test_ai_failure_retains_confirmed_user_and_persists_no_assistant(ai_outcome: object) -> None:
    record = consultation()
    persisted_user = message(record.id, MessageRole.USER, "Question")
    service, _, message_repository, ai_service = service_with(record, history=[persisted_user])
    message_repository.persist_message.return_value = persisted_user
    message_repository.persist_message.side_effect = None
    if isinstance(ai_outcome, Exception):
        ai_service.generate_response.side_effect = ai_outcome
    else:
        ai_service.generate_response.return_value = ai_outcome

    with pytest.raises(AIGenerationError) as caught:
        service.submit_message(record.id, "Question")

    assert caught.value.user_message is persisted_user
    assert "provider detail" not in str(caught.value)
    assert message_repository.persist_message.call_count == 1


def test_assistant_persistence_failure_is_not_reported_as_success() -> None:
    record = consultation()
    persisted_user = message(record.id, MessageRole.USER, "Question")
    service, _, message_repository, _ = service_with(record, history=[persisted_user])
    message_repository.persist_message.side_effect = [
        persisted_user,
        RuntimeError("assistant commit failed"),
    ]

    with pytest.raises(RuntimeError, match="assistant commit failed"):
        service.submit_message(record.id, "Question")

    assert message_repository.persist_message.call_count == 2
