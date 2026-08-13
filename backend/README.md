# Backend

Flask API for the AI Consultation Platform. The implemented Consultation
Records feature uses Pydantic DTOs, an application service, a focused
SQLAlchemy repository, Alembic migrations, and PostgreSQL.

## Requirements

- Python 3.12 or later
- PostgreSQL 16 or later
- Docker, when running the PostgreSQL-backed test suite

## Local setup

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
set -a
source .env
set +a
```

The `.env` file is local configuration and must not be committed. Ensure the
configured PostgreSQL database is running before applying migrations or
starting the API.

## Database migrations

```bash
alembic upgrade head
```

## Run the API

```bash
flask --app app:create_app run --host 0.0.0.0 --port 5000
```

Implemented endpoints:

- `GET /api/v1/consultations`
- `GET /api/v1/consultations/{consultation_id}`

## Tests

The persistence and repository tests create an isolated temporary PostgreSQL
container. They do not use application or production data.

```bash
pytest -q tests
```

No AI credentials or external AI service are required by the implemented
Consultation Records feature or its tests.
