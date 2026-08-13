# Frontend Architecture

## Stack

The frontend uses React, TypeScript, React Router, and MUI.

## Organization

The UI is organized by feature. Each feature owns its screens and presentation concerns, while API communication is handled through dedicated API/service modules.

## Responsibilities

- Present the dashboard, consultation records, consultation detail and chat, summaries, and appointment-booking views.
- Use React Router for client-side navigation.
- Use MUI for consistent interface components.
- Call the backend only through the dedicated API/service layer.

## Boundary

The UI must not contain business persistence logic. Persistence and business decisions remain in the backend. This keeps the frontend suitable for the two-day delivery scope without coupling it to database implementation details.
