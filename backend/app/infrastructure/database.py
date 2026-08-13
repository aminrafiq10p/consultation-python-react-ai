"""Infrastructure-owned SQLAlchemy engine and session construction."""

from __future__ import annotations

import os
from collections.abc import Mapping

from sqlalchemy import URL, Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def database_url_from_environment(environ: Mapping[str, str] | None = None) -> str:
    """Build the PostgreSQL URL from the documented project environment."""
    environment = os.environ if environ is None else environ
    database = environment.get("POSTGRES_DB", "consultation_ai")
    user = environment.get("POSTGRES_USER", "postgres")
    password = environment.get("POSTGRES_PASSWORD", "postgres")
    host = environment.get("POSTGRES_HOST", "localhost")
    port = environment.get("POSTGRES_PORT", "5432")
    return URL.create(
        "postgresql+psycopg",
        username=user,
        password=password,
        host=host,
        port=int(port),
        database=database,
    ).render_as_string(hide_password=False)


def create_database_engine(database_url: str) -> Engine:
    """Create the infrastructure-managed SQLAlchemy engine."""
    return create_engine(database_url, pool_pre_ping=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create sessions owned by the infrastructure boundary.

    Callers must use a session context manager or otherwise close the session;
    failed units of work must be rolled back before reuse.
    """
    return sessionmaker(bind=engine, expire_on_commit=False)
