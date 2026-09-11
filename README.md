# AI Consultation Platform

A full-stack, persistent consultation workflow. Users create consultations, hold an AI-assisted conversation, save a summary and recommendations, book an appointment, and review the resulting records and dashboard data.

## Quick start

**Prerequisites:** Docker and Docker Compose.

From the repository root, create the server-side environment file and start the stack:

```bash
cp backend/.env.example backend/.env
docker compose -f compose.yaml up --build
```

Open the application at http://localhost:3000 and the API at http://localhost:5000. Stop the stack with:

```bash
docker compose -f compose.yaml down
```

The default configuration uses the deterministic mock AI provider, so no API key is required for a local review.

## Key features

- **Dashboard:** total consultations, booked appointments, conversion rate, consultation trends, recent activity, and pending clinical reviews.
- **Consultation Records:** persisted records with search, status filtering, and detail navigation.
- **New Consultation:** creates a persisted consultation through the API.
- **AI Consultation Chat:** persists multi-message conversations and uses the consultation context when generating responses.
- **Summary & Recommendations:** persists a generated summary and ordered treatment recommendations, with restart and booking continuation where eligible.
- **Appointment Booking:** captures a selected recommendation, date/time, and location; creates one appointment and transitions the consultation to `BOOKED`.
- **Appointments:** lists persisted appointments and links them back to their consultation.

## Reviewer walkthrough

```text
Dashboard → New Consultation → AI Chat → Summary / Recommendations
→ Book Appointment → Consultation Records → Appointments → Dashboard
```

The same PostgreSQL-backed state is used throughout this workflow: booking creates exactly one appointment, updates the consultation state, and is reflected in Records, Appointments, and Dashboard projections.

## AI and booking architecture

```text
User conversation → AI consultation → booking-intent detection
→ typed application-owned handoff → Summary / Recommendations
→ deterministic booking workflow → persisted Appointment
```

Conversation context and messages are persisted. The application detects booking intent deterministically and turns it into typed, application-controlled state for the UI. The LLM does not create appointments directly; the booking application/service layer is the write authority. This separates conversational AI from business-write authority and protects against duplicate or provider-driven appointment writes.

The AI abstraction supports two configured providers:

- `AI_PROVIDER=mock` is deterministic, network-free, and the default local configuration.
- `AI_PROVIDER=openai` uses OpenAI through the application's LangChain-backed provider with `OPENAI_API_KEY` and optional `OPENAI_MODEL`.

OpenAI response and summary failures are converted to safe API outcomes; the application does not silently switch an OpenAI request to mock output.

## Architecture

| Area | Implementation |
| --- | --- |
| Frontend | React, TypeScript, Vite, Material UI, React Router, feature API services with runtime validation |
| Backend | Flask application factory, REST routes, Pydantic DTOs, application services, and focused repositories |
| Persistence | SQLAlchemy, PostgreSQL, and Alembic migrations |
| AI | Provider-neutral AI service with OpenAI and deterministic mock implementations |
| Infrastructure | Docker Compose for PostgreSQL, backend, and frontend |

Routes validate HTTP input and delegate workflows to application services; repositories own persistence access. The shared application layout, theme, and visual primitives provide consistent loading, empty, and error states across the frontend.

## Persistence model

Important workflow state is stored in PostgreSQL rather than only in frontend state:

- A **Consultation** owns patient/context fields and lifecycle status.
- **Messages** belong to a consultation and preserve the user/assistant conversation.
- A consultation can have one persisted **Summary**.
- Ordered **Recommendations** belong to that summary.
- An **Appointment** links a consultation to a selected recommendation, schedule, and location.

The database enforces one appointment per consultation. A successful booking persists the appointment and changes the linked consultation to `BOOKED` atomically.

## Dashboard

Dashboard data is derived from persisted application records, not fabricated UI data:

- Total consultations and booked appointments
- Conversion rate
- Consultation trends
- Recent activity
- Pending clinical reviews

Trends use persisted lineage timestamps. Recent activity is a read projection, not a separate audit/event subsystem, and pending clinical reviews represent existing `PENDING` consultations.

## Environment configuration

The Compose backend reads `backend/.env`. Start from `backend/.env.example`; keep this file local and never commit credentials.

| Variable | Purpose |
| --- | --- |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | PostgreSQL connection settings |
| `POSTGRES_HOST`, `POSTGRES_PORT` | Database host and port for local backend/Alembic use |
| `FLASK_DEBUG` | Local Flask debug setting |
| `AI_PROVIDER` | `mock` or `openai` |
| `OPENAI_API_KEY` | Required only when `AI_PROVIDER=openai` |
| `OPENAI_MODEL` | Optional OpenAI model; defaults to `gpt-4.1-mini` |

For OpenAI, use safe placeholders only:

```dotenv
AI_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1-mini
```

The optional root `.env` controls Compose values such as `FRONTEND_PORT`, `BACKEND_PORT`, and `POSTGRES_PORT`. Without overrides, Compose publishes frontend on 3000, backend on 5000, and PostgreSQL on 5440.

## Local development

Manual development is supported with Python 3.12+, Node.js 22+, and PostgreSQL 16+.

Backend, from `backend/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
.venv/bin/alembic upgrade head
flask --app app:create_app run --host 0.0.0.0 --port 5000
```

Set `POSTGRES_HOST=localhost` in the local backend environment. For the frontend, from `frontend/`:

```bash
npm install
npm run dev
```

Manual Vite development normally uses http://localhost:5173; the Docker frontend uses http://localhost:3000.

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/v1/dashboard` | Dashboard metrics and persisted read projections |
| POST, GET | `/api/v1/consultations` | Create and list consultations |
| GET | `/api/v1/consultations/{consultation_id}` | Read consultation detail |
| GET, POST | `/api/v1/consultations/{consultation_id}/messages` | Read and submit persisted chat |
| GET, POST | `/api/v1/consultations/{consultation_id}/summary` | Read or generate a summary |
| POST | `/api/v1/consultations/{consultation_id}/restart` | Restart an eligible consultation |
| POST | `/api/v1/consultations/{consultation_id}/appointments` | Create an appointment |
| GET | `/api/v1/appointments` | List persisted appointments |

## Testing

Backend persistence and integration tests use an isolated Docker PostgreSQL container.

```bash
cd backend && .venv/bin/pytest -q tests
cd frontend && npm test -- --run
cd frontend && npm run typecheck
cd frontend && npm run lint
cd frontend && npm run build
docker compose -f compose.yaml config --quiet
```

## Design decisions and scope

- Workflow state is persistent and server-owned.
- AI behavior is separated from appointment write authority.
- Booking intent produces a deterministic, typed handoff rather than an LLM tool call.
- Dashboard analytics are read projections rather than unnecessary audit infrastructure.
- Visual references guide presentation; they do not introduce fabricated domain data or unsupported workflows.

The application intentionally excludes authentication/admin features, provider scheduling or availability, clinic-management workflows, fabricated pricing/duration/clinical facts, and direct AI appointment writes.
