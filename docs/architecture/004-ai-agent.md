# AI Agent Architecture

## Purpose

The AI layer provides consultation assistance, recommendations, and summaries while remaining isolated from Flask routes and deterministic business operations.

## Flow

```text
Flask API
  ↓
Consultation Service
  ↓
AI Service
  ↓
Consultation Agent
  ↓
Skills
  ↓
Tools where appropriate
  ↓
LangChain
  ↓
AI Provider
  ├── Mock Provider
  └── OpenAI Provider
```

## Components

- **Consultation Agent:** coordinates AI-assisted consultation interactions.
- **Consultation Skill:** supports consultation-oriented responses.
- **Recommendation Skill:** produces recommendation assistance.
- **Summary Skill:** produces consultation summaries.
- **AI provider abstraction:** separates core AI behavior from provider-specific integration.

## Requirements and Optional Integrations

- LangChain is used only inside the AI layer for agent, tool, and LLM orchestration.
- `MockAIProvider` is mandatory so the application runs without an external AI API.
- `OpenAIProvider` is optional.
- Azure OpenAI may be added later through the provider abstraction; it is optional.
- Dynamic conversation branching is optional.
- LLMs must not autonomously create appointments; appointment creation is deterministic.
