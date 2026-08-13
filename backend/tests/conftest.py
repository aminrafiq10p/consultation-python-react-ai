"""Test support for deterministic PostgreSQL-backed persistence tests."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _run_docker(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", *arguments],
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture(scope="session")
def postgresql_url() -> str:
    """Provide an isolated, temporary local PostgreSQL database for tests."""
    container_name = f"consultation-test-{uuid4().hex}"

    container_id = _run_docker(
        "run",
        "--detach",
        "--name",
        container_name,
        "--publish",
        "127.0.0.1::5432",
        "--env",
        "POSTGRES_DB=consultation_test",
        "--env",
        "POSTGRES_USER=postgres",
        "--env",
        "POSTGRES_PASSWORD=postgres",
        "postgres:16-alpine",
    ).stdout.strip()

    try:
        deadline = time.monotonic() + 30

        while time.monotonic() < deadline:
            ready = subprocess.run(
                [
                    "docker",
                    "exec",
                    container_id,
                    "pg_isready",
                    "-U",
                    "postgres",
                    "-d",
                    "consultation_test",
                ],
                capture_output=True,
                text=True,
            )

            if ready.returncode == 0:
                break

            time.sleep(0.25)
        else:
            logs = subprocess.run(
                ["docker", "logs", container_id],
                capture_output=True,
                text=True,
            )

            pytest.fail(
                "Temporary PostgreSQL test container did not become ready.\n"
                f"{logs.stdout}\n"
                f"{logs.stderr}"
            )

        port = _run_docker(
            "inspect",
            "--format",
            "{{(index (index .NetworkSettings.Ports \"5432/tcp\") 0).HostPort}}",
            container_id,
        ).stdout.strip()

        database_url = (
            f"postgresql+psycopg://postgres:postgres@"
            f"127.0.0.1:{port}/consultation_test"
        )

        # Verify an actual client connection before returning the URL. The
        # container-local readiness probe can succeed briefly before the
        # published port accepts connections on the host.
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import OperationalError

        engine = create_engine(database_url, pool_pre_ping=True)
        while time.monotonic() < deadline:
            try:
                with engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                break
            except OperationalError:
                time.sleep(0.25)
        else:
            logs = subprocess.run(
                ["docker", "logs", container_id],
                capture_output=True,
                text=True,
            )
            pytest.fail(
                "Temporary PostgreSQL test container did not accept a client "
                "connection.\n"
                f"{logs.stdout}\n"
                f"{logs.stderr}"
            )
        engine.dispose()

        yield database_url

    finally:
        _run_docker("rm", "--force", container_id)
