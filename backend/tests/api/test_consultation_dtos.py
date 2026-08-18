"""Pydantic DTO coverage for the consultation read API."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.api.consultation_dtos import (
    AppointmentBookingRequest,
    AppointmentRecommendationResponse,
    AppointmentResponse,
    ConsultationDetailPath,
    ConsultationListQuery,
    ConsultationListResponse,
    ConsultationResponse,
    MessageExchangeResponse,
    MessageListResponse,
    MessageResponse,
    MessageSubmissionRequest,
    RecommendationResponse,
    SummaryResponse,
)
from app.infrastructure.consultation_models import ConsultationStatus, MessageRole


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


def test_message_submission_normalizes_content_after_trimming() -> None:
    assert MessageSubmissionRequest(content="  hello  ").content == "hello"
    assert MessageSubmissionRequest(content=f" {'x' * 4_000} ").content == "x" * 4_000


@pytest.mark.parametrize("content", ["", "   ", "\t\n", "x" * 4_001])
def test_message_submission_rejects_invalid_content(content: str) -> None:
    with pytest.raises(ValidationError):
        MessageSubmissionRequest(content=content)


def test_message_dtos_have_exact_approved_shapes() -> None:
    message = MessageResponse(
        id=uuid4(),
        consultation_id=uuid4(),
        role=MessageRole.ASSISTANT,
        content="Answer",
        structured_payload={"topics": ["pain", 2]},
        created_at=datetime(2026, 8, 13, tzinfo=UTC),
    )
    item = message.model_dump(mode="json")

    assert set(item) == {
        "id",
        "consultation_id",
        "role",
        "content",
        "structured_payload",
        "created_at",
    }
    assert item["role"] == "ASSISTANT"
    assert item["structured_payload"] == {"topics": ["pain", 2]}
    assert set(MessageListResponse(items=[message]).model_dump()) == {"items"}
    assert set(
        MessageExchangeResponse(
            user_message=message, assistant_message=message
        ).model_dump()
    ) == {"user_message", "assistant_message"}


def test_summary_dtos_have_exact_approved_shapes() -> None:
    recommendation = RecommendationResponse(
        id=uuid4(), treatment="Physical therapy", position=1
    )
    response = SummaryResponse(
        id=uuid4(),
        consultation_id=uuid4(),
        patient_summary="Persistent knee pain after activity.",
        recommended_treatments=[recommendation],
        recommendation_rationale=None,
        created_at=datetime(2026, 8, 17, tzinfo=UTC),
    ).model_dump(mode="json")

    assert set(response) == {
        "id",
        "consultation_id",
        "patient_summary",
        "recommended_treatments",
        "recommendation_rationale",
        "created_at",
    }
    assert set(response["recommended_treatments"][0]) == {
        "id",
        "treatment",
        "position",
    }
    assert response["recommendation_rationale"] is None


@pytest.mark.parametrize(
    "scheduled_at",
    [
        123,
        "not-a-date",
        "2026-02-30T10:00:00Z",
        "2026-08-20",
        "2026-08-20T14:30:00",
        "2026-08-20T14:30:00+0500",
    ],
)
def test_appointment_request_rejects_invalid_datetime(scheduled_at: object) -> None:
    with pytest.raises(ValidationError):
        AppointmentBookingRequest(
            recommendation_id=uuid4(),
            scheduled_at=scheduled_at,  # type: ignore[arg-type]
            location="Clinic",
        )


@pytest.mark.parametrize(
    ("source", "expected_offset"),
    [("2026-08-20T14:30:00Z", 0), ("2026-08-20T19:30:00+05:00", 18_000)],
)
def test_appointment_request_accepts_explicit_offset_datetime(
    source: str, expected_offset: int
) -> None:
    request = AppointmentBookingRequest(
        recommendation_id=uuid4(), scheduled_at=source, location="  Clinic  "
    )

    assert request.scheduled_at.utcoffset() is not None
    assert request.scheduled_at.utcoffset().total_seconds() == expected_offset
    assert request.location == "Clinic"


@pytest.mark.parametrize("location", ["", "   ", "x" * 201, 123])
def test_appointment_request_rejects_invalid_location(location: object) -> None:
    with pytest.raises(ValidationError):
        AppointmentBookingRequest(
            recommendation_id=uuid4(),
            scheduled_at="2026-08-20T14:30:00Z",
            location=location,  # type: ignore[arg-type]
        )


def test_appointment_request_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        AppointmentBookingRequest.model_validate(
            {
                "recommendation_id": str(uuid4()),
                "scheduled_at": "2026-08-20T14:30:00Z",
                "location": "Clinic",
                "treatment": "must not be accepted",
            }
        )


def test_appointment_response_has_exact_safe_shape_and_offsets() -> None:
    response = AppointmentResponse(
        id=uuid4(),
        consultation_id=uuid4(),
        recommendation=AppointmentRecommendationResponse(
            id=uuid4(), treatment="Physical therapy"
        ),
        scheduled_at=datetime(2026, 8, 20, 14, 30, tzinfo=UTC),
        location="Clinic",
        created_at=datetime(2026, 8, 18, 12, 0, tzinfo=UTC),
    ).model_dump(mode="json")

    assert set(response) == {
        "id",
        "consultation_id",
        "recommendation",
        "scheduled_at",
        "location",
        "created_at",
    }
    assert set(response["recommendation"]) == {"id", "treatment"}
    assert response["scheduled_at"].endswith("Z")
    assert response["created_at"].endswith("Z")
