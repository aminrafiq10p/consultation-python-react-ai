"""AP-005 request-scoped composition coverage for appointment reads."""

from __future__ import annotations

from unittest.mock import Mock

import app as app_module


class SessionDouble:
    """Small session seam sufficient to inspect production composition."""

    def __init__(self) -> None:
        self.close_calls = 0
        self.commit_calls = 0
        self.add_calls = 0
        self.delete_calls = 0

    def close(self) -> None:
        self.close_calls += 1

    def commit(self) -> None:
        self.commit_calls += 1

    def add(self, _value) -> None:
        self.add_calls += 1

    def delete(self, _value) -> None:
        self.delete_calls += 1


def test_production_appointment_list_uses_the_request_session_and_is_read_only(
    monkeypatch,
) -> None:
    session = SessionDouble()
    appointment_repositories: list[Mock] = []

    def build_appointment_repository(repository_session):
        repository = Mock()
        repository._session = repository_session
        repository.list_appointments.return_value = []
        appointment_repositories.append(repository)
        return repository

    monkeypatch.setattr(app_module, "database_url_from_environment", lambda: "url")
    monkeypatch.setattr(app_module, "create_database_engine", lambda _url: object())
    monkeypatch.setattr(
        app_module, "create_session_factory", lambda _engine: lambda: session
    )
    monkeypatch.setattr(app_module, "create_ai_service", lambda _environment: object())
    monkeypatch.setattr(
        app_module, "AppointmentRepository", build_appointment_repository
    )

    application = app_module.create_app()
    application.config.update(TESTING=True)

    with application.test_client() as client:
        response = client.get("/api/v1/appointments")

    assert response.status_code == 200
    assert response.get_json() == {"items": []}
    assert len(appointment_repositories) == 1
    appointment_repository = appointment_repositories[0]
    assert appointment_repository._session is session
    appointment_repository.list_appointments.assert_called_once_with()
    assert session.commit_calls == 0
    assert session.add_calls == 0
    assert session.delete_calls == 0
    assert session.close_calls == 1
    assert "consultation_session" not in application.extensions


def test_injected_consultation_service_remains_the_list_route_boundary(monkeypatch) -> None:
    service = Mock()
    service.list_appointments.return_value = []
    forbidden = Mock(side_effect=AssertionError("production dependency constructed"))
    monkeypatch.setattr(app_module, "create_database_engine", forbidden)
    monkeypatch.setattr(app_module, "create_ai_service", forbidden)

    application = app_module.create_app(consultation_service=service)
    application.config.update(TESTING=True)

    response = application.test_client().get("/api/v1/appointments")

    assert response.status_code == 200
    assert response.get_json() == {"items": []}
    service.list_appointments.assert_called_once_with()
    forbidden.assert_not_called()
