"""Pydantic DTOs for the dashboard API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DashboardResponse(BaseModel):
    """Exact public representation of current dashboard metrics."""

    model_config = ConfigDict(extra="forbid")

    total_consultations: int = Field(strict=True, ge=0)
    booked_appointments: int = Field(strict=True, ge=0)
    conversion_rate: float = Field(
        strict=True,
        ge=0.0,
        le=100.0,
        allow_inf_nan=False,
    )
