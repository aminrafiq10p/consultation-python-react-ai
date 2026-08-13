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

The frontend currently needs no environment values. Its API service sends
same-origin requests to `/api/v1`, so local development must make that path
reach the Flask backend, for example through the approved composed runtime when
its infrastructure implementation is available.

To start Vite directly:

```bash
npm exec vite
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
