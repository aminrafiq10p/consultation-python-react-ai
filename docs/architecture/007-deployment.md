# Deployment Architecture

## Runtime

Docker Compose is mandatory project infrastructure. The complete platform consists of:

- a frontend container;
- a backend container; and
- a PostgreSQL container.

The target startup command is:

```bash
docker compose up --build
```

## Requirements

All implementation dependencies must be containerizable, and Docker Compose support must remain working throughout development. The mock AI provider enables a complete local runtime without an external AI API.

## Optional Services

OpenAI and Azure OpenAI integrations are optional. Azure deployment is not required for this project.
