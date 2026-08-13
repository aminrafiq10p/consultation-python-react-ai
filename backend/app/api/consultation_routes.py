"""Flask routes for consultation records and persisted messages."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from app.api.consultation_dtos import (
    ConsultationDetailPath,
    ConsultationListQuery,
    ConsultationListResponse,
    ConsultationResponse,
    MessageExchangeResponse,
    MessageListResponse,
    MessageResponse,
    MessageSubmissionRequest,
)
from app.application.consultation_service import (
    AIGenerationError,
    ConsultationApplicationService,
    ConsultationNotFoundError,
)

consultation_blueprint = Blueprint("consultations", __name__)


def _service() -> ConsultationApplicationService:
    return current_app.extensions["consultation_service"]


def _validation_error() -> tuple[dict[str, str], int]:
    return {"error": "Invalid request"}, 400


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

    response = MessageListResponse(
        items=[MessageResponse.model_validate(item) for item in messages]
    )
    return jsonify(response.model_dump(mode="json"))


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
    except AIGenerationError as error:
        user_message = MessageResponse.model_validate(error.user_message)
        return {
            "error": "Assistant response is temporarily unavailable",
            "code": "AI_GENERATION_FAILED",
            "user_message": user_message.model_dump(mode="json"),
        }, 503

    response = MessageExchangeResponse(
        user_message=MessageResponse.model_validate(exchange.user_message),
        assistant_message=MessageResponse.model_validate(exchange.assistant_message),
    )
    return jsonify(response.model_dump(mode="json"))
