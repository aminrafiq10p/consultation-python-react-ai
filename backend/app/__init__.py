"""Backend Flask application composition."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from sqlalchemy.orm import Session
from werkzeug.exceptions import HTTPException

from app.ai import create_ai_service
from app.api.consultation_routes import consultation_blueprint
from app.application.consultation_service import ConsultationApplicationService
from app.infrastructure.database import (
    create_database_engine,
    create_session_factory,
    database_url_from_environment,
)
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.summary_repository import SummaryRepository

BACKEND_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


def create_app(
    consultation_service: ConsultationApplicationService | None = None,
) -> Flask:
    """Create the Flask application with production or injected dependencies."""
    load_dotenv(BACKEND_ENV_FILE, override=False)
    app = Flask(__name__)
    CORS(
        app,
        resources={
            r"/api/v1/*": {
                "origins": os.environ.get(
                    "FRONTEND_ORIGIN", "http://localhost:3000"
                )
            }
        },
    )
    app.config["OPENAI_API_KEY_CONFIGURED"] = bool(
        os.environ.get("OPENAI_API_KEY", "").strip()
    )

    if consultation_service is not None:
        app.extensions["consultation_service"] = consultation_service
    else:
        engine = create_database_engine(database_url_from_environment())
        session_factory: Callable[[], Session] = create_session_factory(engine)
        ai_service = create_ai_service(os.environ)
        app.extensions["database_engine"] = engine

        @app.before_request
        def open_consultation_session() -> None:
            session = session_factory()
            app.extensions["consultation_session"] = session
            app.extensions["consultation_service"] = ConsultationApplicationService(
                ConsultationRepository(session),
                MessageRepository(session),
                ai_service,
                SummaryRepository(session),
            )

        @app.teardown_request
        def close_consultation_session(_error: BaseException | None) -> None:
            session = app.extensions.pop("consultation_session", None)
            app.extensions.pop("consultation_service", None)
            if session is not None:
                session.close()

    app.register_blueprint(consultation_blueprint, url_prefix="/api/v1")

    @app.errorhandler(Exception)
    def handle_unexpected_error(_error: Exception):
        if isinstance(_error, HTTPException):
            return _error
        return {"error": "Internal server error"}, 500

    return app
