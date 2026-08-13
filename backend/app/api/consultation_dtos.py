"""Pydantic DTOs for the consultation read API."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.infrastructure.consultation_models import ConsultationStatus


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
    
