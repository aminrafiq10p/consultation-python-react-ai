"""Application-owned booking handoffs and their message JSONB boundary."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.infrastructure.consultation_models import MessageRole


class BookingHandoffAction(str, Enum):
    CONTINUE_CONSULTATION = "CONTINUE_CONSULTATION"
    GENERATE_SUMMARY = "GENERATE_SUMMARY"
    VIEW_SUMMARY = "VIEW_SUMMARY"
    VIEW_APPOINTMENTS = "VIEW_APPOINTMENTS"


class BookingHandoff(BaseModel):
    """Validated, application-owned next action for an assistant message."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["BOOKING_HANDOFF"] = "BOOKING_HANDOFF"
    action: BookingHandoffAction
    consultation_id: UUID
    target: str


_ACTION_TARGETS = {
    BookingHandoffAction.CONTINUE_CONSULTATION: "consultation",
    BookingHandoffAction.GENERATE_SUMMARY: "consultation",
    BookingHandoffAction.VIEW_SUMMARY: "summary",
    BookingHandoffAction.VIEW_APPOINTMENTS: "appointments",
}
_ACTION_MARKER = "_application_handoff_action"
_CONSULTATION_MARKER = "_application_handoff_consultation_id"
_RESERVED_MARKERS = {_ACTION_MARKER, _CONSULTATION_MARKER}


def _target(action: BookingHandoffAction, consultation_id: UUID) -> str:
    if _ACTION_TARGETS[action] == "appointments":
        return "/appointments"
    suffix = "/summary" if _ACTION_TARGETS[action] == "summary" else ""
    return f"/consultations/{consultation_id}{suffix}"


def make_booking_handoff(action: BookingHandoffAction, consultation_id: UUID) -> BookingHandoff:
    return BookingHandoff(
        action=action, consultation_id=consultation_id, target=_target(action, consultation_id)
    )


def encode_handoff_markers(
    provider_payload: dict[str, Any] | None, handoff: BookingHandoff | None
) -> dict[str, Any] | None:
    """Combine provider data with reserved flat markers for assistant storage."""
    payload = {k: v for k, v in (provider_payload or {}).items() if k not in _RESERVED_MARKERS}
    if handoff is not None:
        payload[_ACTION_MARKER] = handoff.action.value
        payload[_CONSULTATION_MARKER] = str(handoff.consultation_id)
    return payload or None


def decode_handoff_markers(
    payload: object, role: MessageRole, consultation_id: UUID
) -> BookingHandoff | None:
    """Decode markers defensively; malformed, mismatched, or user markers fail closed."""
    if role is not MessageRole.ASSISTANT or not isinstance(payload, dict):
        return None
    if not (_ACTION_MARKER in payload or _CONSULTATION_MARKER in payload):
        return None
    try:
        action = BookingHandoffAction(payload[_ACTION_MARKER])
        marker_id = UUID(str(payload[_CONSULTATION_MARKER]))
        if marker_id != consultation_id:
            return None
        handoff = make_booking_handoff(action, consultation_id)
        return handoff if handoff.target == _target(action, consultation_id) else None
    except (KeyError, TypeError, ValueError):
        return None


def project_message_payload(
    payload: object, role: MessageRole, consultation_id: UUID
) -> tuple[dict[str, Any] | None, BookingHandoff | None]:
    """Separate provider payload from reserved markers for the API projection."""
    provider_payload = (
        {key: value for key, value in payload.items() if key not in _RESERVED_MARKERS}
        if isinstance(payload, dict)
        else None
    )
    return provider_payload or None, decode_handoff_markers(payload, role, consultation_id)
