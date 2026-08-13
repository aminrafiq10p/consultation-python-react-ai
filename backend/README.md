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
```

The Flask application loads `backend/.env` automatically for local development
without overriding variables already present in the process environment. The
`.env` file is local configuration and must not be committed. Ensure the
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

AI-layer tests use deterministic doubles and never call OpenAI. Server-side AI
configuration uses `AI_PROVIDER=openai`, `OPENAI_API_KEY`, and optional
`OPENAI_MODEL` (default `gpt-4.1-mini`). Use `AI_PROVIDER=mock` for deterministic
local/test composition. These values must never be exposed through React or a
`VITE_*` variable.

To check credential presence without displaying the secret, inspect
`app.config["OPENAI_API_KEY_CONFIGURED"]`; it contains only a boolean.
