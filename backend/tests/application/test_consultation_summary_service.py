"""CS-005 consultation-summary application workflow coverage."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.ai import AIService, SummaryResult
from app.application.consultation_service import (
    ConsultationApplicationService,
    ConsultationConversationClosedError,
    ConsultationNotFoundError,
    ConsultationNotRestartableError,
    SummaryGenerationError,
    SummaryNotAvailableError,
    SummaryNotEligibleError,
)
from app.infrastructure.consultation_models import (
    Consultation,
    ConsultationStatus,
    Message,
    MessageRole,
)
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.summary_repository import (
    SummaryAggregate,
    SummaryCompletion,
    SummaryRepository,
)


def consultation(status: ConsultationStatus = ConsultationStatus.PENDING) -> Consultation:
    return Consultation(
        id=uuid4(),
        patient_name="Ada Lovelace",
        primary_concern="Persistent knee pain",
        recommended_procedure="Clinical assessment",
        status=status,
    )


def message(record: Consultation, role: MessageRole, content: str) -> Message:
    return Message(
        id=uuid4(),
        consultation_id=record.id,
        role=role,
        content=content,
        structured_payload=None,
    )


def aggregate(record: Consultation) -> SummaryAggregate:
    return SimpleNamespace(
        summary=SimpleNamespace(id=uuid4(), consultation_id=record.id),
        recommendations=(SimpleNamespace(id=uuid4(), treatment="Physiotherapy"),),
    )


def service_with(
    record: Consultation | None,
    *,
    history: list[Message] | None = None,
    persisted_summary: SummaryAggregate | None = None,
    ai_result: object | None = None,
) -> tuple[ConsultationApplicationService, Mock, Mock, Mock, Mock]:
    records = Mock(spec=ConsultationRepository)
    records.get_consultation_by_id.return_value = record
    records.create_consultation.side_effect = lambda item: item
    messages = Mock(spec=MessageRepository)
    messages.list_messages.return_value = history or []
    messages.persist_message.side_effect = lambda item: item
    ai = Mock(spec=AIService)
    ai.generate_summary.return_value = ai_result or SummaryResult(
        "Patient reports knee pain.", ("Physiotherapy",), None
    )
    summaries = Mock(spec=SummaryRepository)
    summaries.get_summary.return_value = persisted_summary
    return (
        ConsultationApplicationService(records, messages, ai, summaries),
        records,
        messages,
        ai,
        summaries,
    )


def test_get_summary_returns_persisted_aggregate_without_ai() -> None:
    record = consultation(ConsultationStatus.COMPLETED)
    expected = aggregate(record)
    service, _, _, ai, summaries = service_with(record, persisted_summary=expected)

    assert service.get_summary(record.id) is expected
    summaries.get_summary.assert_called_once_with(record.id)
    ai.generate_summary.assert_not_called()


def test_get_summary_requires_consultation_and_persisted_summary() -> None:
    missing_id = uuid4()
    service, _, _, ai, summaries = service_with(None)
    with pytest.raises(ConsultationNotFoundError):
        service.get_summary(missing_id)
    summaries.get_summary.assert_not_called()
    ai.generate_summary.assert_not_called()

    record = consultation(ConsultationStatus.COMPLETED)
    service, _, _, ai, _ = service_with(record)
    with pytest.raises(SummaryNotAvailableError):
        service.get_summary(record.id)
    ai.generate_summary.assert_not_called()


def test_existing_summary_bypasses_status_history_and_ai() -> None:
    record = consultation(ConsultationStatus.COMPLETED)
    expected = aggregate(record)
    service, _, messages, ai, summaries = service_with(
        record, persisted_summary=expected
    )

    result = service.generate_summary(record.id)

    assert result.aggregate is expected
    assert result.created is False
    messages.list_messages.assert_not_called()
    ai.generate_summary.assert_not_called()
    summaries.complete_consultation.assert_not_called()


@pytest.mark.parametrize(
    ("status", "roles"),
    [
        (ConsultationStatus.PENDING, []),
        (ConsultationStatus.PENDING, [MessageRole.USER]),
        (ConsultationStatus.PENDING, [MessageRole.ASSISTANT]),
        (ConsultationStatus.PENDING, [MessageRole.ASSISTANT, MessageRole.USER]),
        (ConsultationStatus.BOOKED, [MessageRole.USER, MessageRole.ASSISTANT]),
        (ConsultationStatus.COMPLETED, [MessageRole.USER, MessageRole.ASSISTANT]),
    ],
)
def test_ineligible_generation_never_calls_ai_or_completion(
    status: ConsultationStatus, roles: list[MessageRole]
) -> None:
    record = consultation(status)
    history = [message(record, role, role.value) for role in roles]
    service, _, _, ai, summaries = service_with(record, history=history)

    with pytest.raises(SummaryNotEligibleError):
        service.generate_summary(record.id)

    ai.generate_summary.assert_not_called()
    summaries.complete_consultation.assert_not_called()


def test_missing_consultation_generation_stops_before_other_dependencies() -> None:
    consultation_id = uuid4()
    service, _, messages, ai, summaries = service_with(None)
    with pytest.raises(ConsultationNotFoundError):
        service.generate_summary(consultation_id)
    summaries.get_summary.assert_not_called()
    messages.list_messages.assert_not_called()
    ai.generate_summary.assert_not_called()


def test_generation_forwards_complete_ordered_history_and_delegates_completion() -> None:
    record = consultation()
    history = [
        message(
            record,
            MessageRole.USER if index % 2 == 0 else MessageRole.ASSISTANT,
            (f"message-{index}-" + "x" * 1_100),
        )
        for index in range(22)
    ]
    persisted = aggregate(record)
    service, _, _, ai, summaries = service_with(
        record,
        history=history,
        ai_result=SimpleNamespace(
            patient_summary="  Patient summary  ",
            recommended_treatments=["  Second  ", " First "],
            recommendation_rationale="  Because appropriate  ",
        ),
    )
    summaries.complete_consultation.return_value = SummaryCompletion(
        aggregate=persisted, created=True
    )

    result = service.generate_summary(record.id)

    context, sent = ai.generate_summary.call_args.args
    assert context.consultation_id == str(record.id)
    assert len(sent) == 22
    assert sum(len(item.content) for item in sent) > 24_000
    assert [(item.role, item.content) for item in sent] == [
        (item.role.value, item.content) for item in history
    ]
    summaries.complete_consultation.assert_called_once_with(
        record,
        patient_summary="Patient summary",
        recommended_treatments=("Second", "First"),
        recommendation_rationale="Because appropriate",
    )
    assert result.aggregate is persisted
    assert result.created is True
    assert record.status is ConsultationStatus.PENDING
    assert record.recommended_procedure == "Clinical assessment"


def test_generation_preserves_repository_race_result() -> None:
    record = consultation()
    history = [
        message(record, MessageRole.USER, "Question"),
        message(record, MessageRole.ASSISTANT, "Answer"),
    ]
    winner = aggregate(record)
    service, _, _, _, summaries = service_with(record, history=history)
    summaries.complete_consultation.return_value = SummaryCompletion(
        aggregate=winner, created=False
    )

    result = service.generate_summary(record.id)

    assert result.aggregate is winner
    assert result.created is False


@pytest.mark.parametrize(
    "outcome",
    [
        RuntimeError("raw provider detail"),
        SimpleNamespace(
            patient_summary=" ",
            recommended_treatments=("Treatment",),
            recommendation_rationale=None,
        ),
        SimpleNamespace(
            patient_summary="Summary",
            recommended_treatments=(),
            recommendation_rationale=None,
        ),
        SimpleNamespace(
            patient_summary="Summary",
            recommended_treatments=(" ",),
            recommendation_rationale=None,
        ),
        SimpleNamespace(
            patient_summary="Summary",
            recommended_treatments=("Treatment",),
            recommendation_rationale=" ",
        ),
    ],
)
def test_ai_or_validation_failure_is_safe_and_does_not_persist(outcome: object) -> None:
    record = consultation()
    history = [
        message(record, MessageRole.USER, "Question"),
        message(record, MessageRole.ASSISTANT, "Answer"),
    ]
    service, _, _, ai, summaries = service_with(record, history=history)
    if isinstance(outcome, Exception):
        ai.generate_summary.side_effect = outcome
    else:
        ai.generate_summary.return_value = outcome

    with pytest.raises(SummaryGenerationError) as caught:
        service.generate_summary(record.id)

    assert "raw provider detail" not in str(caught.value)
    summaries.complete_consultation.assert_not_called()
    assert record.status is ConsultationStatus.PENDING
    assert record.recommended_procedure == "Clinical assessment"


@pytest.mark.parametrize(
    "status", [ConsultationStatus.COMPLETED, ConsultationStatus.BOOKED]
)
def test_closed_consultation_rejects_message_before_persistence_and_ai(
    status: ConsultationStatus,
) -> None:
    record = consultation(status)
    service, _, messages, ai, _ = service_with(record)

    with pytest.raises(ConsultationConversationClosedError):
        service.submit_message(record.id, "Question")

    messages.persist_message.assert_not_called()
    messages.list_messages.assert_not_called()
    ai.generate_response.assert_not_called()


@pytest.mark.parametrize("status", [ConsultationStatus.PENDING, ConsultationStatus.BOOKED])
def test_non_completed_consultation_is_not_restartable(status: ConsultationStatus) -> None:
    record = consultation(status)
    service, records, _, _, _ = service_with(record)
    with pytest.raises(ConsultationNotRestartableError):
        service.restart_consultation(record.id)
    records.create_consultation.assert_not_called()


def test_completed_without_summary_is_not_restartable() -> None:
    record = consultation(ConsultationStatus.COMPLETED)
    service, records, _, _, _ = service_with(record)
    with pytest.raises(ConsultationNotRestartableError):
        service.restart_consultation(record.id)
    records.create_consultation.assert_not_called()


def test_restart_creates_exact_fresh_consultation_without_mutating_source() -> None:
    source = consultation(ConsultationStatus.COMPLETED)
    source_values = (
        source.id,
        source.patient_name,
        source.primary_concern,
        source.recommended_procedure,
        source.status,
    )
    service, records, messages, ai, summaries = service_with(
        source, persisted_summary=aggregate(source)
    )

    restarted = service.restart_consultation(source.id)

    assert restarted.id != source.id
    assert restarted.patient_name == source.patient_name
    assert restarted.primary_concern == source.primary_concern
    assert restarted.recommended_procedure == ""
    assert restarted.status is ConsultationStatus.PENDING
    assert source_values == (
        source.id,
        source.patient_name,
        source.primary_concern,
        source.recommended_procedure,
        source.status,
    )
    records.create_consultation.assert_called_once_with(restarted)
    summaries.get_summary.assert_called_once_with(source.id)
    assert messages.method_calls == []
    assert ai.method_calls == []


def test_restart_missing_source_does_not_create() -> None:
    service, records, _, _, summaries = service_with(None)
    with pytest.raises(ConsultationNotFoundError):
        service.restart_consultation(uuid4())
    records.create_consultation.assert_not_called()
    summaries.get_summary.assert_not_called()
