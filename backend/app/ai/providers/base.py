"""Small provider-neutral values and provider protocol."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping, Protocol, Sequence, TypeAlias

JSONScalar: TypeAlias = str | int | float | bool | None
StructuredPayload: TypeAlias = dict[str, JSONScalar | list[JSONScalar]]


def _is_json_scalar(value: object) -> bool:
    return (
        value is None
        or isinstance(value, (str, bool, int))
        or (isinstance(value, float) and isfinite(value))
    )


def validate_structured_payload(payload: object) -> StructuredPayload:
    if not isinstance(payload, dict):
        raise ValueError("structured payload must be an object")

    validated: StructuredPayload = {}
    for key, value in payload.items():
        if not isinstance(key, str):
            raise ValueError("structured payload keys must be strings")
        if _is_json_scalar(value):
            validated[key] = value
        elif isinstance(value, list) and all(_is_json_scalar(item) for item in value):
            validated[key] = list(value)
        else:
            raise ValueError("structured payload values must be scalars or scalar arrays")
    return validated


@dataclass(frozen=True)
class AIResult:
    content: str
    structured_payload: StructuredPayload | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("assistant content must be nonblank")
        object.__setattr__(self, "content", self.content.strip())
        if self.structured_payload is not None:
            object.__setattr__(
                self,
                "structured_payload",
                validate_structured_payload(self.structured_payload),
            )


@dataclass(frozen=True)
class ConversationMessage:
    role: str
    content: str

    def __post_init__(self) -> None:
        normalized_role = self.role.strip().upper() if isinstance(self.role, str) else ""
        if normalized_role not in {"USER", "ASSISTANT"}:
            raise ValueError("conversation role must be USER or ASSISTANT")
        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("conversation content must be nonblank")
        object.__setattr__(self, "role", normalized_role)
        object.__setattr__(self, "content", self.content.strip())


@dataclass(frozen=True)
class ConsultationContext:
    consultation_id: str
    primary_concern: str
    display_fields: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.consultation_id, str) or not self.consultation_id.strip():
            raise ValueError("consultation id must be nonblank")
        if not isinstance(self.primary_concern, str) or not self.primary_concern.strip():
            raise ValueError("primary concern must be nonblank")


@dataclass(frozen=True)
class ProviderRequest:
    system_instruction: str
    consultation_context: ConsultationContext
    messages: Sequence[ConversationMessage]


class ProviderError(RuntimeError):
    """Internal provider failure; never exposed beyond the AI layer."""


class AIProvider(Protocol):
    def generate(self, request: ProviderRequest) -> AIResult: ...
