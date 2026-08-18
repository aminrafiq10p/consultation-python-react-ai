"""Flask route for read-only dashboard metrics."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.api.dashboard_dtos import DashboardResponse
from app.application.dashboard_service import DashboardApplicationService

dashboard_blueprint = Blueprint("dashboard", __name__)


def _service() -> DashboardApplicationService:
    return current_app.extensions["dashboard_service"]


@dashboard_blueprint.get("/dashboard")
def get_dashboard():
    """Return current persisted dashboard metrics without accepting input."""
    if request.args or request.get_data(cache=True):
        return {"error": "Invalid request"}, 400

    metrics = _service().get_metrics()
    response = DashboardResponse(
        total_consultations=metrics.total_consultations,
        booked_appointments=metrics.booked_appointments,
        conversion_rate=float(metrics.conversion_rate),
    )
    return jsonify(response.model_dump(mode="json"))
