from uuid import uuid4

import pytest

from app.application.booking_handoff import (
    BookingHandoff,
    BookingHandoffAction,
    decode_handoff_markers,
    encode_handoff_markers,
    make_booking_handoff,
    project_message_payload,
)
from app.infrastructure.consultation_models import MessageRole


@pytest.mark.parametrize("action", list(BookingHandoffAction))
def test_valid_actions_round_trip_with_exact_targets(action):
    consultation_id = uuid4()
    handoff = make_booking_handoff(action, consultation_id)

    stored = encode_handoff_markers({"provider": "value"}, handoff)
    provider_payload, projected = project_message_payload(
        stored, MessageRole.ASSISTANT, consultation_id
    )

    assert projected == handoff
    assert provider_payload == {"provider": "value"}
    expected = "/appointments" if action is BookingHandoffAction.VIEW_APPOINTMENTS else f"/consultations/{consultation_id}"
    if action is BookingHandoffAction.VIEW_SUMMARY:
        expected += "/summary"
    assert handoff.target == expected


@pytest.mark.parametrize(
    "payload",
    [
        {"_application_handoff_action": "NOPE", "_application_handoff_consultation_id": str(uuid4())},
        {"_application_handoff_action": "VIEW_SUMMARY", "_application_handoff_consultation_id": "not-a-uuid"},
        {"_application_handoff_action": "VIEW_SUMMARY"},
        {"_application_handoff_consultation_id": str(uuid4())},
    ],
)
def test_malformed_markers_fail_closed(payload):
    assert decode_handoff_markers(payload, MessageRole.ASSISTANT, uuid4()) is None


def test_mismatched_and_user_markers_fail_closed():
    consultation_id = uuid4()
    handoff = make_booking_handoff(BookingHandoffAction.GENERATE_SUMMARY, consultation_id)
    stored = encode_handoff_markers({}, handoff)

    assert decode_handoff_markers(stored, MessageRole.ASSISTANT, uuid4()) is None
    assert decode_handoff_markers(stored, MessageRole.USER, consultation_id) is None


@pytest.mark.parametrize(
    "payload",
    [
        {"type": "NOT_A_HANDOFF", "action": "VIEW_SUMMARY", "consultation_id": str(uuid4()), "target": "/appointments"},
        {"type": "BOOKING_HANDOFF", "action": "VIEW_SUMMARY", "consultation_id": str(uuid4()), "target": "/appointments", "appointment_id": str(uuid4())},
    ],
)
def test_typed_handoff_rejects_invalid_contract_fields(payload):
    with pytest.raises(ValueError):
        BookingHandoff.model_validate(payload)


def test_legacy_and_provider_payloads_are_preserved_and_markers_stripped():
    consultation_id = uuid4()
    payload, handoff = project_message_payload(
        {"topics": ["pain", 2]}, MessageRole.ASSISTANT, consultation_id
    )
    assert payload == {"topics": ["pain", 2]}
    assert handoff is None

    stored = encode_handoff_markers(
        {"topics": ["pain"], "_application_handoff_action": "spoof"},
        make_booking_handoff(BookingHandoffAction.VIEW_SUMMARY, consultation_id),
    )
    assert stored["_application_handoff_action"] == "VIEW_SUMMARY"
