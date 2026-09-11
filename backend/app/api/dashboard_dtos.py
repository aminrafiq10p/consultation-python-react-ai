"""Pydantic DTOs for the dashboard API."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.infrastructure.consultation_models import ConsultationStatus


class DashboardTrendResponse(BaseModel):
    """API representation of one populated daily trend bucket."""

    model_config = ConfigDict(extra="forbid")

    day: date
    consultation_count: int = Field(strict=True, ge=1)


class DashboardActivityResponse(BaseModel):
    """API representation of one supported recent activity item."""

    model_config = ConfigDict(extra="forbid")

    activity_type: Literal[
        "conversation_started", "consultation_completed", "appointment_booked"
    ]
    consultation_id: UUID
    timestamp: datetime


class DashboardPendingClinicalReviewResponse(BaseModel):
    """API representation of one pending consultation projection."""

    model_config = ConfigDict(extra="forbid")

    consultation_id: UUID
    patient_name: str = Field(strict=True, min_length=1)
    primary_concern: str = Field(strict=True, min_length=1)
    recommended_procedure: str = Field(strict=True)
    status: ConsultationStatus


class DashboardResponse(BaseModel):
    """Exact public representation of metrics and dashboard projections."""

    model_config = ConfigDict(extra="forbid")

    total_consultations: int = Field(strict=True, ge=0)
    booked_appointments: int = Field(strict=True, ge=0)
    conversion_rate: float = Field(
        strict=True,
        ge=0.0,
        le=100.0,
        allow_inf_nan=False,
    )
    consultation_trends: list[DashboardTrendResponse]
    recent_activity: list[DashboardActivityResponse]
    pending_clinical_reviews: list[DashboardPendingClinicalReviewResponse]
