# Frontend

React and TypeScript frontend for the AI Consultation Platform. The implemented
Consultation Records feature provides list and detail views using React Router,
Material UI, and a dedicated consultation API service.

## Requirements

- Node.js 20 or later
- npm

## Local setup

From the repository root:

```bash
cd frontend
npm ci
```

Copy `.env.example` to `.env` when running Vite directly. The dedicated API
service prepends the browser-safe `VITE_API_BASE_URL` value to `/api/v1`
requests. Do not place database values, AI provider settings, or secrets in a
`VITE_*` variable.

To start Vite directly:

```bash
npm run dev
```

## Checks

```bash
npm test
npm run typecheck
npm run lint
npm run build
```

Frontend tests use deterministic service and transport doubles. They do not
require a live Flask API, PostgreSQL instance, external AI service, or OpenAI
credentials.

## Application boundaries

- Feature components call the dedicated consultation service.
- Components do not call PostgreSQL or external AI providers.
- Persisted consultation data comes from the backend API.
- Backend secrets must never be added to frontend environment variables.
