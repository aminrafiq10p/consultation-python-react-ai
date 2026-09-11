"""Flask route for read-only dashboard metrics."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.api.dashboard_dtos import (
    DashboardActivityResponse,
    DashboardPendingClinicalReviewResponse,
    DashboardResponse,
    DashboardTrendResponse,
)
from app.application.dashboard_service import DashboardApplicationService

dashboard_blueprint = Blueprint("dashboard", __name__)


def _service() -> DashboardApplicationService:
    return current_app.extensions["dashboard_service"]


@dashboard_blueprint.get("/dashboard")
def get_dashboard():
    """Return current persisted dashboard metrics without accepting input."""
    if request.args or request.get_data(cache=True):
        return {"error": "Invalid request"}, 400

    dashboard = _service().get_dashboard()
    metrics = dashboard.metrics
    response = DashboardResponse(
        total_consultations=metrics.total_consultations,
        booked_appointments=metrics.booked_appointments,
        conversion_rate=float(metrics.conversion_rate),
        consultation_trends=[
            DashboardTrendResponse(
                day=item.day,
                consultation_count=item.consultation_count,
            )
            for item in dashboard.consultation_trends
        ],
        recent_activity=[
            DashboardActivityResponse(
                activity_type=item.activity_type,
                consultation_id=item.consultation_id,
                timestamp=item.timestamp,
            )
            for item in dashboard.recent_activity
        ],
        pending_clinical_reviews=[
            DashboardPendingClinicalReviewResponse(
                consultation_id=item.consultation_id,
                patient_name=item.patient_name,
                primary_concern=item.primary_concern,
                recommended_procedure=item.recommended_procedure,
                status=item.status,
            )
            for item in dashboard.pending_clinical_reviews
        ],
    )
    return jsonify(response.model_dump(mode="json"))
