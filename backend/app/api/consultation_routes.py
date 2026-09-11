"""Flask routes for consultation records and persisted messages."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from app.api.consultation_dtos import (
    AppointmentBookingRequest,
    AppointmentListItemResponse,
    AppointmentListRecommendationResponse,
    AppointmentListResponse,
    AppointmentRecommendationResponse,
    AppointmentResponse,
    ConsultationCreationRequest,
    ConsultationDetailPath,
    ConsultationListQuery,
    ConsultationListResponse,
    ConsultationResponse,
    MessageResponse,
    MessageSubmissionRequest,
    RecommendationResponse,
    SummaryResponse,
)
from app.application.consultation_service import (
    AIGenerationError,
    AppointmentAlreadyExistsError,
    ConsultationApplicationService,
    ConsultationConversationClosedError,
    InvalidConsultationCreationError,
    ConsultationNotFoundError,
    ConsultationNotBookableError,
    ConsultationNotRestartableError,
    InvalidAppointmentBookingError,
    RecommendationNotBookableError,
    RecommendationNotFoundError,
    SummaryGenerationError,
    SummaryNotAvailableError,
    SummaryNotEligibleError,
)
from app.application.booking_handoff import project_message_payload
from app.repositories.summary_repository import SummaryAggregate

consultation_blueprint = Blueprint("consultations", __name__)


def _service() -> ConsultationApplicationService:
    return current_app.extensions["consultation_service"]


def _validation_error() -> tuple[dict[str, str], int]:
    return {"error": "Invalid request"}, 400


def _has_request_body() -> bool:
    return bool(request.get_data(cache=True))


def _summary_response(aggregate: SummaryAggregate) -> SummaryResponse:
    return SummaryResponse(
        id=aggregate.summary.id,
        consultation_id=aggregate.summary.consultation_id,
        patient_summary=aggregate.summary.patient_summary,
        recommended_treatments=[
            RecommendationResponse.model_validate(item)
            for item in aggregate.recommendations
        ],
        recommendation_rationale=aggregate.summary.recommendation_rationale,
        created_at=aggregate.summary.created_at,
    )


def _message_response(message) -> dict:
    """Project provider data and app-owned handoffs at the API boundary."""
    structured_payload, handoff = project_message_payload(
        message.structured_payload,
        message.role,
        message.consultation_id,
    )
    response = MessageResponse.model_validate(message).model_copy(
        update={"structured_payload": structured_payload, "handoff": handoff}
    )
    body = response.model_dump(mode="json")
    if handoff is None:
        body.pop("handoff")
    return body


@consultation_blueprint.post("/consultations")
def create_consultation():
    """Validate and persist one new pending consultation."""
    if request.args or request.mimetype != "application/json":
        return _validation_error()

    try:
        body = ConsultationCreationRequest.model_validate(request.get_json(silent=True))
    except ValidationError:
        return _validation_error()

    try:
        consultation = _service().create_consultation(
            body.patient_name,
            body.primary_concern,
        )
    except InvalidConsultationCreationError:
        return _validation_error()

    response = ConsultationResponse.model_validate(consultation)
    return jsonify(response.model_dump(mode="json")), 201


@consultation_blueprint.post("/consultations/<consultation_id>/appointments")
def book_consultation_appointment(consultation_id: str):
    """Create one persisted appointment for an eligible consultation."""
    try:
        path = ConsultationDetailPath(consultation_id=consultation_id)
        body = AppointmentBookingRequest.model_validate(request.get_json(silent=True))
    except ValidationError:
        return _validation_error()

    try:
        aggregate = _service().book_appointment(
            path.consultation_id,
            body.recommendation_id,
            body.scheduled_at,
            body.location,
        )
    except InvalidAppointmentBookingError:
        return _validation_error()
    except ConsultationNotFoundError:
        return {"error": "Consultation not found"}, 404
    except RecommendationNotFoundError:
        return {"error": "Recommendation not found"}, 404
    except RecommendationNotBookableError:
        return {
            "error": "Recommendation is not bookable",
            "code": "RECOMMENDATION_NOT_BOOKABLE",
        }, 409
    except ConsultationNotBookableError:
        return {
            "error": "Consultation is not bookable",
            "code": "CONSULTATION_NOT_BOOKABLE",
        }, 409
    except AppointmentAlreadyExistsError:
        return {
            "error": "Appointment already exists",
            "code": "APPOINTMENT_ALREADY_EXISTS",
        }, 409

    response = AppointmentResponse(
        id=aggregate.appointment.id,
        consultation_id=aggregate.appointment.consultation_id,
        recommendation=AppointmentRecommendationResponse.model_validate(
            aggregate.recommendation
        ),
        scheduled_at=aggregate.appointment.scheduled_at,
        location=aggregate.appointment.location,
        created_at=aggregate.appointment.created_at,
    )
    return jsonify(response.model_dump(mode="json")), 201


@consultation_blueprint.get("/appointments")
def list_appointments():
    """Return every persisted appointment using the approved read contract."""
    if request.args or _has_request_body():
        return _validation_error()

    appointments = _service().list_appointments()
    response = AppointmentListResponse(
        items=[
            AppointmentListItemResponse(
                id=item.id,
                consultation_id=item.consultation_id,
                patient_name=item.patient_name,
                recommendation=AppointmentListRecommendationResponse(
                    id=item.recommendation_id,
                    treatment=item.treatment,
                ),
                scheduled_at=item.scheduled_at,
                location=item.location,
                created_at=item.created_at,
            )
            for item in appointments
        ]
    )
    return jsonify(response.model_dump(mode="json"))


@consultation_blueprint.get("/consultations")
def list_consultations():
    """Return consultations matching validated optional criteria."""
    try:
        query = ConsultationListQuery.model_validate(request.args.to_dict())
    except ValidationError:
        return _validation_error()

    consultations = _service().list_consultations(
        search=query.search,
        status=query.status,
    )
    response = ConsultationListResponse(
        items=[ConsultationResponse.model_validate(item) for item in consultations]
    )
    return jsonify(response.model_dump(mode="json"))


@consultation_blueprint.get("/consultations/<consultation_id>")
def get_consultation(consultation_id: str):
    """Return one consultation identified by a validated UUID."""
    try:
        path = ConsultationDetailPath(consultation_id=consultation_id)
    except ValidationError:
        return _validation_error()

    try:
        consultation = _service().get_consultation(path.consultation_id)
    except ConsultationNotFoundError:
        return {"error": "Consultation not found"}, 404

    response = ConsultationResponse.model_validate(consultation)
    return jsonify(response.model_dump(mode="json"))


@consultation_blueprint.get("/consultations/<consultation_id>/messages")
def get_consultation_messages(consultation_id: str):
    """Return an existing consultation's persisted conversation history."""
    try:
        path = ConsultationDetailPath(consultation_id=consultation_id)
    except ValidationError:
        return _validation_error()

    try:
        messages = _service().get_messages(path.consultation_id)
    except ConsultationNotFoundError:
        return {"error": "Consultation not found"}, 404

    return jsonify({"items": [_message_response(item) for item in messages]})


@consultation_blueprint.get("/consultations/<consultation_id>/summary")
def get_consultation_summary(consultation_id: str):
    """Return an existing persisted summary without generating one."""
    try:
        path = ConsultationDetailPath(consultation_id=consultation_id)
    except ValidationError:
        return _validation_error()

    try:
        aggregate = _service().get_summary(path.consultation_id)
    except ConsultationNotFoundError:
        return {"error": "Consultation not found"}, 404
    except SummaryNotAvailableError:
        return {
            "error": "Consultation summary is not available",
            "code": "SUMMARY_NOT_AVAILABLE",
        }, 409

    response = _summary_response(aggregate)
    return jsonify(response.model_dump(mode="json"))


@consultation_blueprint.post("/consultations/<consultation_id>/summary")
def generate_consultation_summary(consultation_id: str):
    """Generate or return the one persisted consultation summary."""
    try:
        path = ConsultationDetailPath(consultation_id=consultation_id)
    except ValidationError:
        return _validation_error()
    if _has_request_body():
        return _validation_error()

    try:
        result = _service().generate_summary(path.consultation_id)
    except ConsultationNotFoundError:
        return {"error": "Consultation not found"}, 404
    except SummaryNotEligibleError:
        return {
            "error": "Consultation is not eligible for summary generation",
            "code": "SUMMARY_NOT_ELIGIBLE",
        }, 409
    except SummaryGenerationError:
        return {
            "error": "Consultation summary is temporarily unavailable",
            "code": "SUMMARY_GENERATION_FAILED",
        }, 503

    response = _summary_response(result.aggregate)
    return jsonify(response.model_dump(mode="json")), 201 if result.created else 200


@consultation_blueprint.post("/consultations/<consultation_id>/restart")
def restart_consultation(consultation_id: str):
    """Create a fresh pending consultation from a completed source."""
    try:
        path = ConsultationDetailPath(consultation_id=consultation_id)
    except ValidationError:
        return _validation_error()
    if _has_request_body():
        return _validation_error()

    try:
        consultation = _service().restart_consultation(path.consultation_id)
    except ConsultationNotFoundError:
        return {"error": "Consultation not found"}, 404
    except ConsultationNotRestartableError:
        return {
            "error": "Consultation cannot be restarted",
            "code": "CONSULTATION_NOT_RESTARTABLE",
        }, 409

    response = ConsultationResponse.model_validate(consultation)
    return jsonify(response.model_dump(mode="json")), 201


@consultation_blueprint.post("/consultations/<consultation_id>/messages")
def submit_consultation_message(consultation_id: str):
    """Submit one message and return the confirmed persisted exchange."""
    try:
        path = ConsultationDetailPath(consultation_id=consultation_id)
        body = MessageSubmissionRequest.model_validate(request.get_json(silent=True))
    except ValidationError:
        return _validation_error()

    try:
        exchange = _service().submit_message(path.consultation_id, body.content)
    except ConsultationNotFoundError:
        return {"error": "Consultation not found"}, 404
    except ConsultationConversationClosedError:
        return {
            "error": "Consultation conversation is closed",
            "code": "CONSULTATION_CONVERSATION_CLOSED",
        }, 409
    except AIGenerationError as error:
        user_message = _message_response(error.user_message)
        return {
            "error": "Assistant response is temporarily unavailable",
            "code": "AI_GENERATION_FAILED",
            "user_message": user_message,
        }, 503

    return jsonify(
        {
            "user_message": _message_response(exchange.user_message),
            "assistant_message": _message_response(exchange.assistant_message),
        }
    )
