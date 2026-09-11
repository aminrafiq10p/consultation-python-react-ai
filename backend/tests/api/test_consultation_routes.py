"""HTTP-boundary tests for consultation record reads."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from app import create_app
from app.application.consultation_service import (
    AIGenerationError,
    ConsultationApplicationService,
    ConsultationConversationClosedError,
    ConsultationNotFoundError,
    ConsultationNotRestartableError,
    InvalidConsultationCreationError,
    GeneratedSummary,
    PersistedExchange,
    SummaryGenerationError,
    SummaryNotAvailableError,
    SummaryNotEligibleError,
)
from app.infrastructure.consultation_models import (
    ConsultationRecommendation,
    ConsultationStatus,
    ConsultationSummary,
    MessageRole,
)
from app.repositories.summary_repository import SummaryAggregate


def consultation(**overrides):
    values = {
        "id": uuid4(),
        "patient_name": "Amina Khan",
        "primary_concern": "Knee pain",
        "recommended_procedure": "Physical therapy",
        "status": ConsultationStatus.PENDING,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def message(consultation_id, role, content, *, offset=0, payload=None):
    return SimpleNamespace(
        id=uuid4(),
        consultation_id=consultation_id,
        role=role,
        content=content,
        structured_payload=payload,
        created_at=datetime(2026, 8, 13, tzinfo=UTC) + timedelta(seconds=offset),
    )


def summary_aggregate(consultation_id):
    summary = ConsultationSummary(
        id=uuid4(),
        consultation_id=consultation_id,
        patient_summary="Persistent knee pain after activity.",
        recommendation_rationale=None,
        created_at=datetime(2026, 8, 17, tzinfo=UTC),
    )
    recommendations = (
        ConsultationRecommendation(
            id=uuid4(), summary_id=summary.id, treatment="Physical therapy", position=1
        ),
        ConsultationRecommendation(
            id=uuid4(), summary_id=summary.id, treatment="Activity modification", position=2
        ),
    )
    return SummaryAggregate(summary=summary, recommendations=recommendations)


@pytest.fixture
def service() -> Mock:
    return Mock(spec=ConsultationApplicationService)


@pytest.fixture
def client(service: Mock):
    app = create_app(service)
    app.config.update(TESTING=True)
    return app.test_client()


def test_list_success_has_approved_five_field_shape(client, service: Mock) -> None:
    record = consultation()
    service.list_consultations.return_value = [record]

    response = client.get("/api/v1/consultations")

    assert response.status_code == 200
    assert response.get_json() == {
        "items": [
            {
                "id": str(record.id),
                "patient_name": "Amina Khan",
                "primary_concern": "Knee pain",
                "recommended_procedure": "Physical therapy",
                "status": "PENDING",
            }
        ]
    }
    service.list_consultations.assert_called_once_with(search=None, status=None)


def test_empty_list_is_successful(client, service: Mock) -> None:
    service.list_consultations.return_value = []

    response = client.get("/api/v1/consultations")

    assert response.status_code == 200
    assert response.get_json() == {"items": []}


def test_create_consultation_returns_exact_persisted_response(client, service: Mock) -> None:
    record = consultation(
        primary_concern="Persistent knee pain",
        recommended_procedure="",
        status=ConsultationStatus.PENDING,
    )
    service.create_consultation.return_value = record

    response = client.post(
        "/api/v1/consultations",
        json={
            "patient_name": "  Amina Khan  ",
            "primary_concern": "  Persistent knee pain  ",
        },
    )

    assert response.status_code == 201
    assert response.get_json() == {
        "id": str(record.id),
        "patient_name": "Amina Khan",
        "primary_concern": "Persistent knee pain",
        "recommended_procedure": "",
        "status": "PENDING",
    }
    service.create_consultation.assert_called_once_with(
        "Amina Khan", "Persistent knee pain"
    )


@pytest.mark.parametrize(
    ("path", "kwargs"),
    [
        ("/api/v1/consultations?unexpected=value", {"json": {"patient_name": "A", "primary_concern": "C"}}),
        ("/api/v1/consultations", {}),
        ("/api/v1/consultations", {"data": "", "content_type": "application/json"}),
        ("/api/v1/consultations", {"data": "{", "content_type": "application/json"}),
        ("/api/v1/consultations", {"json": None}),
        ("/api/v1/consultations", {"json": []}),
        ("/api/v1/consultations", {"json": "value"}),
        ("/api/v1/consultations", {"json": {}}),
        ("/api/v1/consultations", {"json": {"patient_name": "A"}}),
        ("/api/v1/consultations", {"json": {"primary_concern": "C"}}),
        ("/api/v1/consultations", {"json": {"patient_name": " ", "primary_concern": "C"}}),
        ("/api/v1/consultations", {"json": {"patient_name": "A", "primary_concern": "\t"}}),
        ("/api/v1/consultations", {"json": {"patient_name": "x" * 201, "primary_concern": "C"}}),
        ("/api/v1/consultations", {"json": {"patient_name": "A", "primary_concern": "x" * 4_001}}),
        ("/api/v1/consultations", {"json": {"patient_name": 1, "primary_concern": "C"}}),
        ("/api/v1/consultations", {"json": {"patient_name": True, "primary_concern": "C"}}),
        ("/api/v1/consultations", {"json": {"patient_name": ["A"], "primary_concern": "C"}}),
        ("/api/v1/consultations", {"json": {"patient_name": {"name": "A"}, "primary_concern": "C"}}),
        ("/api/v1/consultations", {"json": {"patient_name": "A", "primary_concern": "C", "id": str(uuid4())}}),
        ("/api/v1/consultations", {"json": {"patient_name": "A", "primary_concern": "C", "status": "PENDING"}}),
        ("/api/v1/consultations", {"json": {"patient_name": "A", "primary_concern": "C", "recommended_procedure": ""}}),
        ("/api/v1/consultations", {"data": '{"patient_name":"A","primary_concern":"C"}', "content_type": "text/plain"}),
    ],
)
def test_create_consultation_rejects_invalid_input_without_service_call(
    client, service: Mock, path: str, kwargs: dict[str, object]
) -> None:
    response = client.post(path, **kwargs)

    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid request"}
    service.create_consultation.assert_not_called()


def test_create_consultation_maps_defensive_application_input_to_400(
    client, service: Mock
) -> None:
    service.create_consultation.side_effect = InvalidConsultationCreationError

    response = client.post(
        "/api/v1/consultations",
        json={"patient_name": "Amina Khan", "primary_concern": "Knee pain"},
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid request"}


@pytest.mark.parametrize("failure", [RuntimeError("postgresql://user:secret@db"), ValueError("serialization failed")])
def test_create_consultation_unexpected_failure_returns_safe_500(
    client, service: Mock, failure: Exception
) -> None:
    service.create_consultation.side_effect = failure

    response = client.post(
        "/api/v1/consultations",
        json={"patient_name": "Amina Khan", "primary_concern": "Knee pain"},
    )

    assert response.status_code == 500
    assert response.get_json() == {"error": "Internal server error"}
    assert str(failure) not in response.get_data(as_text=True)


def test_create_consultation_serialization_failure_returns_safe_500(
    client, service: Mock
) -> None:
    service.create_consultation.return_value = SimpleNamespace(id=uuid4())

    response = client.post(
        "/api/v1/consultations",
        json={"patient_name": "Amina Khan", "primary_concern": "Knee pain"},
    )

    assert response.status_code == 500
    assert response.get_json() == {"error": "Internal server error"}
    assert "primary_concern" not in response.get_data(as_text=True)


@pytest.mark.parametrize(
    ("query", "search", "status"),
    [
        ("search=%20%20knee%20%20", "  knee  ", None),
        ("status=BOOKED", None, ConsultationStatus.BOOKED),
        (
            "search=therapy&status=COMPLETED",
            "therapy",
            ConsultationStatus.COMPLETED,
        ),
    ],
)
def test_valid_filters_are_forwarded_unchanged(
    client, service: Mock, query: str, search: str | None, status
) -> None:
    service.list_consultations.return_value = []

    response = client.get(f"/api/v1/consultations?{query}")

    assert response.status_code == 200
    service.list_consultations.assert_called_once_with(search=search, status=status)


@pytest.mark.parametrize("query", ["search=", "search=%20%20%20", "status=UNKNOWN"])
def test_invalid_list_input_returns_400(client, service: Mock, query: str) -> None:
    response = client.get(f"/api/v1/consultations?{query}")

    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid request"}
    service.list_consultations.assert_not_called()


def test_detail_success(client, service: Mock) -> None:
    record = consultation(status=ConsultationStatus.BOOKED)
    service.get_consultation.return_value = record

    response = client.get(f"/api/v1/consultations/{record.id}")

    assert response.status_code == 200
    assert set(response.get_json()) == {
        "id",
        "patient_name",
        "primary_concern",
        "recommended_procedure",
        "status",
    }
    service.get_consultation.assert_called_once_with(record.id)


def test_invalid_detail_uuid_returns_400(client, service: Mock) -> None:
    response = client.get("/api/v1/consultations/not-a-uuid")

    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid request"}
    service.get_consultation.assert_not_called()


def test_missing_detail_returns_404(client, service: Mock) -> None:
    consultation_id = uuid4()
    service.get_consultation.side_effect = ConsultationNotFoundError

    response = client.get(f"/api/v1/consultations/{consultation_id}")

    assert response.status_code == 404
    assert response.get_json() == {"error": "Consultation not found"}


@pytest.mark.parametrize("endpoint", ["list", "detail"])
def test_unexpected_service_failure_returns_safe_500(
    client, service: Mock, endpoint: str
) -> None:
    internal_detail = "postgresql://user:secret@db SQL SELECT consultations"
    if endpoint == "list":
        service.list_consultations.side_effect = RuntimeError(internal_detail)
        path = "/api/v1/consultations"
    else:
        service.get_consultation.side_effect = RuntimeError(internal_detail)
        path = f"/api/v1/consultations/{uuid4()}"

    response = client.get(path)

    assert response.status_code == 500
    assert response.get_json() == {"error": "Internal server error"}
    assert internal_detail not in response.get_data(as_text=True)


def test_message_history_success_has_order_and_exact_dto_shape(client, service: Mock) -> None:
    consultation_id = uuid4()
    history = [
        message(consultation_id, MessageRole.USER, "Question"),
        message(
            consultation_id,
            MessageRole.ASSISTANT,
            "Answer",
            offset=1,
            payload={"topics": ["pain", 2]},
        ),
    ]
    service.get_messages.return_value = history

    response = client.get(f"/api/v1/consultations/{consultation_id}/messages")

    assert response.status_code == 200
    body = response.get_json()
    assert [item["content"] for item in body["items"]] == ["Question", "Answer"]
    assert set(body["items"][0]) == {
        "id", "consultation_id", "role", "content", "structured_payload", "created_at"
    }
    assert body["items"][1]["structured_payload"] == {"topics": ["pain", 2]}
    service.get_messages.assert_called_once_with(consultation_id)


def test_empty_message_history_is_successful(client, service: Mock) -> None:
    consultation_id = uuid4()
    service.get_messages.return_value = []
    response = client.get(f"/api/v1/consultations/{consultation_id}/messages")
    assert response.status_code == 200
    assert response.get_json() == {"items": []}


@pytest.mark.parametrize("method", ["get", "post"])
def test_message_routes_reject_invalid_uuid(client, service: Mock, method: str) -> None:
    response = getattr(client, method)(
        "/api/v1/consultations/not-a-uuid/messages", json={"content": "Hello"}
    )
    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid request"}
    service.get_messages.assert_not_called()
    service.submit_message.assert_not_called()


@pytest.mark.parametrize("method", ["get", "post"])
def test_message_routes_return_404_for_missing_consultation(
    client, service: Mock, method: str
) -> None:
    consultation_id = uuid4()
    getattr(service, "get_messages" if method == "get" else "submit_message").side_effect = (
        ConsultationNotFoundError
    )
    response = getattr(client, method)(
        f"/api/v1/consultations/{consultation_id}/messages", json={"content": "Hello"}
    )
    assert response.status_code == 404
    assert response.get_json() == {"error": "Consultation not found"}


def test_message_submission_returns_confirmed_exchange_and_normalized_content(
    client, service: Mock
) -> None:
    consultation_id = uuid4()
    user = message(consultation_id, MessageRole.USER, "Question")
    assistant = message(
        consultation_id,
        MessageRole.ASSISTANT,
        "Answer",
        offset=1,
        payload={"items": ["one", 2]},
    )
    service.submit_message.return_value = PersistedExchange(user, assistant)

    response = client.post(
        f"/api/v1/consultations/{consultation_id}/messages",
        json={"content": "  Question  "},
    )

    assert response.status_code == 200
    assert response.get_json()["user_message"]["id"] == str(user.id)
    assert response.get_json()["assistant_message"]["structured_payload"] == {
        "items": ["one", 2]
    }
    service.submit_message.assert_called_once_with(consultation_id, "Question")


def test_message_submission_projects_the_persisted_booking_handoff(client, service: Mock) -> None:
    consultation_id = uuid4()
    user = message(consultation_id, MessageRole.USER, "Please book an appointment")
    assistant = message(
        consultation_id,
        MessageRole.ASSISTANT,
        "Use the existing summary workflow for the next step.",
        offset=1,
        payload={
            "_application_handoff_action": "GENERATE_SUMMARY",
            "_application_handoff_consultation_id": str(consultation_id),
        },
    )
    service.submit_message.return_value = PersistedExchange(user, assistant)

    response = client.post(
        f"/api/v1/consultations/{consultation_id}/messages",
        json={"content": "Please book an appointment"},
    )

    assert response.status_code == 200
    assert response.get_json()["assistant_message"]["structured_payload"] is None
    assert response.get_json()["assistant_message"]["handoff"] == {
        "type": "BOOKING_HANDOFF",
        "action": "GENERATE_SUMMARY",
        "consultation_id": str(consultation_id),
        "target": f"/consultations/{consultation_id}",
    }


@pytest.mark.parametrize(
    "body",
    [None, {}, {"content": ""}, {"content": "   "}, {"content": "x" * 4_001},
     {"content": "ok", "extra": True}],
)
def test_message_submission_rejects_invalid_body(client, service: Mock, body) -> None:
    consultation_id = uuid4()
    response = client.post(
        f"/api/v1/consultations/{consultation_id}/messages", json=body
    )
    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid request"}
    service.submit_message.assert_not_called()


def test_ai_failure_returns_safe_503_with_persisted_user(client, service: Mock) -> None:
    consultation_id = uuid4()
    persisted_user = message(consultation_id, MessageRole.USER, "Question")
    service.submit_message.side_effect = AIGenerationError(persisted_user)

    response = client.post(
        f"/api/v1/consultations/{consultation_id}/messages",
        json={"content": "Question"},
    )

    assert response.status_code == 503
    assert response.get_json() == {
        "error": "Assistant response is temporarily unavailable",
        "code": "AI_GENERATION_FAILED",
        "user_message": {
            "id": str(persisted_user.id),
            "consultation_id": str(consultation_id),
            "role": "USER",
            "content": "Question",
            "structured_payload": None,
            "created_at": persisted_user.created_at.isoformat().replace("+00:00", "Z"),
        },
    }


def test_closed_conversation_message_returns_coded_409(client, service: Mock) -> None:
    consultation_id = uuid4()
    service.submit_message.side_effect = ConsultationConversationClosedError

    response = client.post(
        f"/api/v1/consultations/{consultation_id}/messages",
        json={"content": "Question"},
    )

    assert response.status_code == 409
    assert response.get_json() == {
        "error": "Consultation conversation is closed",
        "code": "CONSULTATION_CONVERSATION_CLOSED",
    }


def test_summary_get_returns_exact_ordered_persisted_shape(client, service: Mock) -> None:
    consultation_id = uuid4()
    aggregate = summary_aggregate(consultation_id)
    service.get_summary.return_value = aggregate

    response = client.get(f"/api/v1/consultations/{consultation_id}/summary")

    assert response.status_code == 200
    body = response.get_json()
    assert set(body) == {
        "id", "consultation_id", "patient_summary", "recommended_treatments",
        "recommendation_rationale", "created_at",
    }
    assert [item["position"] for item in body["recommended_treatments"]] == [1, 2]
    assert set(body["recommended_treatments"][0]) == {"id", "treatment", "position"}
    assert body["recommendation_rationale"] is None
    service.get_summary.assert_called_once_with(consultation_id)


@pytest.mark.parametrize("created, status", [(True, 201), (False, 200)])
def test_summary_post_uses_creation_flag(client, service: Mock, created: bool, status: int) -> None:
    consultation_id = uuid4()
    aggregate = summary_aggregate(consultation_id)
    service.generate_summary.return_value = GeneratedSummary(aggregate, created)

    response = client.post(f"/api/v1/consultations/{consultation_id}/summary")

    assert response.status_code == status
    assert response.get_json()["id"] == str(aggregate.summary.id)
    service.generate_summary.assert_called_once_with(consultation_id)


@pytest.mark.parametrize("suffix", ["summary", "restart"])
@pytest.mark.parametrize("data", [b"{}", b" ", b"null"])
def test_no_body_posts_reject_any_supplied_bytes(client, service: Mock, suffix: str, data: bytes) -> None:
    response = client.post(f"/api/v1/consultations/{uuid4()}/{suffix}", data=data)

    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid request"}
    service.generate_summary.assert_not_called()
    service.restart_consultation.assert_not_called()


@pytest.mark.parametrize("method,suffix", [("get", "summary"), ("post", "summary"), ("post", "restart")])
def test_feature_003_routes_reject_invalid_uuid(client, service: Mock, method: str, suffix: str) -> None:
    response = getattr(client, method)(f"/api/v1/consultations/not-a-uuid/{suffix}")
    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid request"}


@pytest.mark.parametrize(
    "method,suffix,target,error,expected",
    [
        ("get", "summary", "get_summary", ConsultationNotFoundError, (404, {"error": "Consultation not found"})),
        ("post", "summary", "generate_summary", ConsultationNotFoundError, (404, {"error": "Consultation not found"})),
        ("post", "restart", "restart_consultation", ConsultationNotFoundError, (404, {"error": "Consultation not found"})),
        ("get", "summary", "get_summary", SummaryNotAvailableError, (409, {"error": "Consultation summary is not available", "code": "SUMMARY_NOT_AVAILABLE"})),
        ("post", "summary", "generate_summary", SummaryNotEligibleError, (409, {"error": "Consultation is not eligible for summary generation", "code": "SUMMARY_NOT_ELIGIBLE"})),
        ("post", "summary", "generate_summary", SummaryGenerationError, (503, {"error": "Consultation summary is temporarily unavailable", "code": "SUMMARY_GENERATION_FAILED"})),
        ("post", "restart", "restart_consultation", ConsultationNotRestartableError, (409, {"error": "Consultation cannot be restarted", "code": "CONSULTATION_NOT_RESTARTABLE"})),
    ],
)
def test_feature_003_typed_errors(client, service: Mock, method, suffix, target, error, expected) -> None:
    getattr(service, target).side_effect = error
    response = getattr(client, method)(f"/api/v1/consultations/{uuid4()}/{suffix}")
    assert response.status_code == expected[0]
    assert response.get_json() == expected[1]


def test_restart_returns_standard_consultation_dto_with_201(client, service: Mock) -> None:
    source_id = uuid4()
    restarted = consultation(recommended_procedure="", status=ConsultationStatus.PENDING)
    service.restart_consultation.return_value = restarted

    response = client.post(f"/api/v1/consultations/{source_id}/restart")

    assert response.status_code == 201
    assert response.get_json() == {
        "id": str(restarted.id),
        "patient_name": restarted.patient_name,
        "primary_concern": restarted.primary_concern,
        "recommended_procedure": "",
        "status": "PENDING",
    }
    service.restart_consultation.assert_called_once_with(source_id)


@pytest.mark.parametrize("method", ["get", "post"])
def test_unexpected_message_failure_returns_safe_500(
    client, service: Mock, method: str
) -> None:
    consultation_id = uuid4()
    internal_detail = "provider=openai key=secret prompt=private SQL INSERT"
    target = service.get_messages if method == "get" else service.submit_message
    target.side_effect = RuntimeError(internal_detail)
    response = getattr(client, method)(
        f"/api/v1/consultations/{consultation_id}/messages", json={"content": "Hello"}
    )
    assert response.status_code == 500
    assert response.get_json() == {"error": "Internal server error"}
    assert internal_detail not in response.get_data(as_text=True)
