"""Composition coverage for the dashboard service boundary."""

from __future__ import annotations

from unittest.mock import Mock

import app as app_module
from app.application.consultation_service import ConsultationApplicationService
from app.application.dashboard_service import DashboardApplicationService
from app.repositories.dashboard_repository import DashboardRepository


class SessionDouble:
    def __init__(self) -> None:
        self.close_calls = 0

    def close(self) -> None:
        self.close_calls += 1


def test_production_services_share_request_session_and_teardown_closes_it(
    monkeypatch,
) -> None:
    session = SessionDouble()
    monkeypatch.setattr(app_module, "database_url_from_environment", lambda: "url")
    monkeypatch.setattr(app_module, "create_database_engine", lambda _url: object())
    monkeypatch.setattr(
        app_module, "create_session_factory", lambda _engine: lambda: session
    )
    monkeypatch.setattr(app_module, "create_ai_service", lambda _environment: object())

    application = app_module.create_app()
    with application.test_request_context("/api/v1/dashboard"):
        application.preprocess_request()
        consultation = application.extensions["consultation_service"]
        dashboard = application.extensions["dashboard_service"]

        assert consultation._repository._session is session
        assert consultation._message_repository._session is session
        assert consultation._summary_repository._session is session
        assert consultation._appointment_repository._session is session
        assert dashboard._repository._session is session
        assert isinstance(dashboard._repository, DashboardRepository)
        assert application.extensions["consultation_session"] is session

        application.do_teardown_request(None)

    assert session.close_calls == 1
    assert "consultation_session" not in application.extensions
    assert "consultation_service" not in application.extensions
    assert "dashboard_service" not in application.extensions


def test_dashboard_injection_does_not_construct_production_dependencies(
    monkeypatch,
) -> None:
    dashboard_service = Mock(spec=DashboardApplicationService)
    forbidden = Mock(side_effect=AssertionError("production dependency constructed"))
    monkeypatch.setattr(app_module, "create_database_engine", forbidden)
    monkeypatch.setattr(app_module, "create_ai_service", forbidden)

    application = app_module.create_app(dashboard_service=dashboard_service)

    assert application.extensions["dashboard_service"] is dashboard_service
    assert "consultation_service" not in application.extensions
    forbidden.assert_not_called()


def test_existing_consultation_injection_remains_compatible(monkeypatch) -> None:
    consultation_service = Mock(spec=ConsultationApplicationService)
    forbidden = Mock(side_effect=AssertionError("production dependency constructed"))
    monkeypatch.setattr(app_module, "create_database_engine", forbidden)
    monkeypatch.setattr(app_module, "create_ai_service", forbidden)

    application = app_module.create_app(consultation_service)

    assert application.extensions["consultation_service"] is consultation_service
    assert "dashboard_service" not in application.extensions
    forbidden.assert_not_called()
