"""Tests for local backend environment loading and secret-safe reporting."""

from __future__ import annotations

import app as app_module
from app import create_app


def test_app_loads_backend_dotenv_without_overriding_process_environment(
    monkeypatch, tmp_path
):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "AI_PROVIDER=mock\nOPENAI_API_KEY=dotenv-secret\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(app_module, "BACKEND_ENV_FILE", env_file)
    monkeypatch.setenv("OPENAI_API_KEY", "process-secret")

    app = create_app(consultation_service=object())

    assert app.config["OPENAI_API_KEY_CONFIGURED"] is True
    assert app_module.os.environ["OPENAI_API_KEY"] == "process-secret"


def test_app_reports_openai_key_presence_as_boolean(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "server-only-secret")

    app = create_app(consultation_service=object())

    assert app.config["OPENAI_API_KEY_CONFIGURED"] is True
    assert "server-only-secret" not in repr(app.config["OPENAI_API_KEY_CONFIGURED"])


def test_app_reports_missing_openai_key(monkeypatch, tmp_path):
    monkeypatch.setattr(app_module, "BACKEND_ENV_FILE", tmp_path / ".env")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    app = create_app(consultation_service=object())

    assert app.config["OPENAI_API_KEY_CONFIGURED"] is False
