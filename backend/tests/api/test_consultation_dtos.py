"""Pydantic DTO coverage for the consultation read API."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.api.consultation_dtos import (
    ConsultationDetailPath,
    ConsultationListQuery,
    ConsultationListResponse,
    ConsultationResponse,
)
from app.infrastructure.consultation_models import ConsultationStatus


def test_list_query_preserves_valid_search_and_status() -> None:
    query = ConsultationListQuery(search="  knee  ", status="PENDING")

    assert query.search == "  knee  "
    assert query.status is ConsultationStatus.PENDING


@pytest.mark.parametrize("search", ["", "   ", "\t\n"])
def test_list_query_rejects_blank_supplied_search(search: str) -> None:
    with pytest.raises(ValidationError):
        ConsultationListQuery(search=search)


def test_list_query_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError):
        ConsultationListQuery(status="CANCELLED")


def test_detail_path_validates_uuid() -> None:
    consultation_id = uuid4()

    assert ConsultationDetailPath(
        consultation_id=str(consultation_id)
    ).consultation_id == consultation_id


def test_response_dtos_have_exact_approved_shape() -> None:
    response = ConsultationListResponse(
        items=[
            ConsultationResponse(
                id=uuid4(),
                patient_name="Amina Khan",
                primary_concern="Knee pain",
                recommended_procedure="Physical therapy",
                status=ConsultationStatus.BOOKED,
            )
        ]
    )

    assert set(response.model_dump(mode="json")) == {"items"}
    assert set(response.model_dump(mode="json")["items"][0]) == {
        "id",
        "patient_name",
        "primary_concern",
        "recommended_procedure",
        "status",
    }
