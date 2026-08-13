"""Pydantic DTOs for the consultation API."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.infrastructure.consultation_models import ConsultationStatus, MessageRole


class ConsultationResponse(BaseModel):
    """API representation of a consultation record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_name: str
    primary_concern: str
    recommended_procedure: str
    status: ConsultationStatus


class ConsultationListResponse(BaseModel):
    """API representation of a consultation collection."""

    items: list[ConsultationResponse]


class ConsultationListQuery(BaseModel):
    """Validated query parameters for consultation listing."""

    model_config = ConfigDict(extra="forbid")

    search: str | None = None
    status: ConsultationStatus | None = None

    @field_validator("search")
    @classmethod
    def validate_search(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("search must not be blank")

        return value


class ConsultationDetailPath(BaseModel):
    """Validated path parameters for consultation detail."""

    model_config = ConfigDict(extra="forbid")

    consultation_id: UUID


class MessageResponse(BaseModel):
    """API representation of one persisted consultation message."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    consultation_id: UUID
    role: MessageRole
    content: str
    structured_payload: dict[str, Any] | None
    created_at: datetime


class MessageListResponse(BaseModel):
    """API representation of a persisted conversation history."""

    items: list[MessageResponse]


class MessageSubmissionRequest(BaseModel):
    """Validated and normalized message submission body."""

    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1, max_length=4_000)

    @field_validator("content", mode="before")
    @classmethod
    def normalize_content(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class MessageExchangeResponse(BaseModel):
    """Confirmed persisted messages from a successful AI exchange."""

    user_message: MessageResponse
    assistant_message: MessageResponse
