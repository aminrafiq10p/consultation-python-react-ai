# AI Consultation Platform

An AI-assisted consultation platform that allows users to conduct consultations, persist conversation history, generate recommendations and summaries, and book appointments.

## Project Status

🚧 In Development

## Core Flow

Dashboard
→ Consultation Records
→ Consultation Detail / AI Chat
→ Consultation Summary
→ Appointment Booking
→ Consultation Records

## Technology Stack

### Frontend

- React
- TypeScript
- Material UI

### Backend

- Python
- Flask
- SQLAlchemy
- Pydantic
- Alembic

### Database

- PostgreSQL

### AI

- LangChain
- Mock AI Provider
- OpenAI Provider (optional)

### Infrastructure

- Docker
- Docker Compose

## Development Approach

This project follows a specification-driven development process.

```text
Architecture
    ↓
Specification
    ↓
Implementation Plan
    ↓
Tasks
    ↓
Implementation
    ↓
Testing
    ↓
Definition of Done
```

## Docker runtime

Copy the safe project-level environment template and adjust only local values:

```bash
cp .env.example .env
docker compose up --build
```

With the defaults, open the frontend at `http://localhost:3000` and the backend
at `http://localhost:5000`. `FRONTEND_PORT` and `BACKEND_PORT` change those host
ports. If port 5432 is already occupied, set `POSTGRES_PORT=5433`; the backend
still connects to PostgreSQL at `postgres:5432` inside Compose.

The default `AI_PROVIDER=mock` needs no external credentials. For an optional
real-provider smoke test, put the key only in the root `.env`; it remains a
backend-only value and is not built into either image.

## Direct backend runtime

For Flask outside Docker, copy `backend/.env.example` to `backend/.env` and keep
`POSTGRES_HOST=localhost`. Then run migrations and Flask from `backend/` as
documented in [backend/README.md](backend/README.md).
