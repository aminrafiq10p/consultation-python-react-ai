# Frontend Foundation Specification

## 1. Purpose and Scope

Define the frontend foundation required before frontend feature development
begins for the AI Consultation Platform. The foundation shall provide a small,
typed React application structure that supports the approved core flow, clear
navigation, consistent UI composition, and controlled communication with the
Flask REST API.

This specification governs future frontend application structure, build
tooling, routing, shared UI responsibilities, API access, browser-safe
configuration, client state, feedback states, testing, and containerization.
It does not define feature screens, UI designs, API endpoint contracts,
backend behavior, schemas, AI prompts, or skills.

This specification authorizes no implementation by itself. Frontend
implementation begins only after this specification is approved and a plan and
tasks are created.

## 2. React and TypeScript Foundation

The frontend shall use React and TypeScript. React shall own client-side
presentation, interaction, and temporary UI state; TypeScript shall provide
typed frontend boundaries and maintainable feature code.

Frontend code shall remain focused on the approved two-day scope. It shall not
contain persistence business logic, backend application rules, direct database
access, LangChain behavior, or AI-provider SDK integration.

## 3. Vite and Build Tooling

Vite shall provide the frontend development and production build tooling. The
tooling shall support the React + TypeScript application and be compatible with
the mandatory Docker Compose runtime.

Build and development configuration shall remain minimal and shall not add
unapproved UI, state-management, or build technologies. This foundation does
not define package manifests, build commands, or configuration files.

## 4. Feature-Oriented Project Structure

The frontend shall use a compact feature-oriented structure. The expected
foundation organization is:

```text
frontend/
├── src/
│   ├── app/
│   │   ├── core/
│   │   ├── shared/
│   │   ├── layout/
│   │   └── features/
│   └── ...
├── public/
├── Dockerfile
└── package.json
```

The `src/app/` areas shall have the following bounded responsibilities:

- `core/` owns application-wide composition such as routing setup,
  browser-safe configuration access, and shared API client/service
  foundations.
- `shared/` owns reusable, presentation-focused elements and common frontend
  utilities with clear ownership. It shall not become an unstructured
  catch-all area.
- `layout/` owns the application shell and shared navigation composition.
- `features/` owns feature-specific screens, presentation components,
  temporary UI state, and feature-facing API/service modules.

Feature tests may be colocated with the code they verify when implementation
begins. A top-level `tests/` directory is not required for this small project
unless a later approved specification establishes a cross-feature testing need.

The exact file and module names may be determined during implementation
planning. They shall preserve feature ownership, a dedicated API/service
boundary, and the separation of core, shared, layout, and feature concerns.

## 5. Routing

React Router shall provide client-side navigation for the approved application
flow. Routing shall be centrally composed and allow feature-owned screens to
be registered without placing feature implementation inside the application
shell.

Routes shall coordinate navigation and layout selection only. They shall not
contain persistence logic, backend business decisions, or direct network
requests. Exact route paths, route parameters, navigation rules, and
feature-specific access behavior require later specifications.

## 6. Layout and Navigation

The frontend shall provide a reusable application layout and navigation
foundation using MUI. The layout shall give the approved core-flow features a
consistent place to render while keeping feature content owned by its feature
area.

Navigation shall use React Router rather than ad hoc browser navigation. This
foundation does not prescribe visual design, navigation labels, individual
screens, or feature-specific interactions.

## 7. API and Service Layer

The frontend shall communicate with the backend only through dedicated API or
service modules. These modules shall own frontend HTTP request construction,
API response translation into frontend-facing data, and transport-level error
handling support.

Feature UI code shall not make direct network requests, access persistence, or
encode backend workflow decisions. API/service modules shall not duplicate
backend domain logic or AI behavior. API endpoint paths, request/response DTO
contracts, authentication requirements, and feature-specific service behavior
require later API and feature specifications.

## 8. Environment Configuration

Frontend configuration shall be externalized and limited to browser-safe
build/runtime values required by the frontend, such as the backend API base
configuration when later specified. Vite-exposed environment values are public
to the browser and shall be treated accordingly.

The frontend shall never contain secrets, database credentials, AI-provider
API keys, or private backend configuration. Configuration access shall be
centralized rather than scattered through feature UI code. New configuration
variables require documentation of their purpose, public exposure, and safe
example value in accordance with the project foundation.

## 9. State Management Approach

Client state management shall remain simple. React component state and context
may be used for temporary UI state and small shared presentation concerns, such
as application layout state, where justified.

No Redux or other global state-management library is required or authorized by
this foundation. The backend remains the source of truth for persisted
consultation and conversation state. A feature may temporarily hold current
interaction state in the browser, including unsent or in-progress chat UI
state, but persisted conversation history shall be obtained from and updated
through the backend API/service layer.

## 10. Forms and Validation

Frontend forms shall provide clear client-side input handling and user-visible
validation feedback appropriate to their feature. Client validation shall
support usability but shall not be treated as the authoritative enforcement of
business rules; the backend API remains responsible for boundary validation and
deterministic decisions.

MUI form controls and React-managed form state are sufficient by default. A
form library is not required or authorized unless a later approved
specification demonstrates a need within the approved scope. Field definitions,
validation rules, and form behaviors belong in later feature specifications.

## 11. Loading and Error Handling

Frontend features that load or submit backend data shall provide explicit UI
states for pending work, successful results where needed, recoverable failures,
and unavailable or missing data as applicable. These states shall be owned by
the relevant feature and use shared presentation patterns only where they are
genuinely common.

Error messages shall be safe and understandable to users. The frontend shall
not expose internal server details, credentials, provider details, or raw
unexpected error payloads. Error presentation shall not replace backend error
handling or deterministic business decisions.

## 12. MUI Usage

MUI is the approved component library for consistent, accessible frontend
composition. The frontend shall use MUI for the application layout, navigation,
forms, feedback states, and reusable interface elements where appropriate.

Additional UI component libraries are not required or authorized. MUI usage
shall remain practical for the two-day scope and avoid a premature custom design
system or unnecessary abstraction layer.

## 13. Testing with React Testing Library

Frontend behavior shall be testable with React Testing Library. Later feature
specifications shall require tests appropriate to changed routing, feature UI
states, form interactions, API/service integration boundaries, and acceptance
criteria.

Tests shall verify user-observable behavior rather than implementation details
where practical. The exact test runner setup, fixtures, mocks, and coverage
expectations require later approved specifications. Frontend testing must not
depend on a live external AI provider.

## 14. Docker and Containerization Requirements

The frontend shall be containerizable and participate in the required Docker
Compose runtime with backend and PostgreSQL services. Its container setup shall
support the Vite-built frontend without relying on host-specific dependencies
or embedding secrets.

Frontend container configuration shall use only browser-safe configuration.
The complete platform shall retain compatibility with the approved
`docker compose up --build` outcome. This foundation does not define a
Dockerfile, Compose service configuration, or build/deployment commands.

## 15. Frontend and Backend Boundary

The Flask REST API is the only boundary between frontend features and backend
application services. The frontend shall interact with it solely through the
dedicated API/service layer.

The frontend shall not access PostgreSQL, repositories, application services,
domain rules, LangChain, or AI-provider implementations. It shall not make
appointment decisions or consultation status transitions independently; it may
request backend operations and present their results. The backend remains the
authority for persistence, business rules, validation, AI orchestration, and
deterministic operations.

## 16. Definition of Done

Frontend foundation implementation work is complete only when all of the
following are satisfied:

- The implemented frontend structure follows this specification, the approved
  project foundation, the frontend architecture, and applicable ADRs.
- A React + TypeScript application has Vite build support, React Router
  composition, and an MUI-based layout/navigation foundation.
- Features are organized by ownership and communicate with the backend only
  through dedicated API/service modules.
- Browser-safe configuration is centralized, and no secrets or AI-provider
  keys are exposed to the frontend.
- Client state remains simple; persisted consultation and conversation state is
  sourced from the backend API.
- Relevant loading, error, form-feedback, and React Testing Library behavior
  are implemented and verified as approved feature work requires.
- The frontend is containerized and remains compatible with the complete Docker
  Compose runtime.
- No unapproved state-management library, UI library, micro-frontend
  architecture, feature contract, or scope expansion is introduced.

## 17. Acceptance Criteria

This frontend foundation specification is accepted when:

- `specs/foundation/002-frontend-foundation.md` exists.
- It defines a small React + TypeScript and Vite foundation for the approved
  two-day delivery scope.
- It defines a justified feature-oriented structure with core, shared, layout,
  and feature responsibilities, without requiring an unnecessary top-level test
  directory.
- It requires React Router for navigation, MUI for consistent UI composition,
  and dedicated API/service modules as the sole frontend-to-backend boundary.
- It requires centralized browser-safe configuration and prohibits secrets,
  database credentials, and AI-provider keys in the frontend.
- It limits state management to React state/context unless a later approved
  specification justifies a change, and it preserves the backend as the source
  of truth for persisted consultation and conversation state.
- It requires appropriate client validation, loading/error feedback, React
  Testing Library support, and Docker Compose-compatible containerization.
- It excludes individual feature UI designs, feature screen details, endpoint
  contracts, backend behavior, schemas, AI prompts or skills, and unapproved
  technologies.
- No frontend source files, package manifests, Dockerfiles, tests,
  configuration files, or architecture/ADR changes are created by this phase.
