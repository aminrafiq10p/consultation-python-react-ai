"""Flask routes for consultation record reads."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from app.api.consultation_dtos import (
    ConsultationDetailPath,
    ConsultationListQuery,
    ConsultationListResponse,
    ConsultationResponse,
)
from app.application.consultation_service import (
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
