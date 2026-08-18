"""Pydantic DTOs for the consultation API."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator

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


class RecommendationResponse(BaseModel):
    """API representation of one persisted ordered recommendation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    treatment: str
    position: int


class SummaryResponse(BaseModel):
    """API representation of one persisted consultation summary aggregate."""

    id: UUID
    consultation_id: UUID
    patient_summary: str
    recommended_treatments: list[RecommendationResponse]
    recommendation_rationale: str | None
    created_at: datetime


class AppointmentBookingRequest(BaseModel):
    """Validated and normalized appointment creation body."""

    model_config = ConfigDict(extra="forbid")

    recommendation_id: UUID
    scheduled_at: datetime
    location: StrictStr = Field(max_length=200)

    @field_validator("scheduled_at", mode="before")
    @classmethod
    def require_explicit_offset_datetime(cls, value: object) -> object:
        if not isinstance(value, str) or not re.search(
            r"(?:Z|[+-]\d{2}:\d{2})$", value
        ):
            raise ValueError("scheduled_at must be an explicit-offset datetime")
        return value

    @field_validator("scheduled_at")
    @classmethod
    def require_aware_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("scheduled_at must be timezone-aware")
        return value

    @field_validator("location", mode="before")
    @classmethod
    def normalize_location(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("location")
    @classmethod
    def require_nonblank_location(cls, value: str) -> str:
        if not value:
            raise ValueError("location must not be blank")
        return value


class AppointmentRecommendationResponse(BaseModel):
    """Authoritative persisted recommendation projection for a booking."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    treatment: str


class AppointmentResponse(BaseModel):
    """API representation returned after an appointment commits."""

    id: UUID
    consultation_id: UUID
    recommendation: AppointmentRecommendationResponse
    scheduled_at: datetime
    location: str
    created_at: datetime

    @field_validator("scheduled_at", "created_at")
    @classmethod
    def require_aware_timestamps(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("appointment timestamps must be timezone-aware")
        return value
