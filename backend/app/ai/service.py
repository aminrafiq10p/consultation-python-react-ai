"""Application-facing AI service and centralized provider composition."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from app.ai.consultation_agent import ConsultationAgent
from app.ai.consultation_skill import ConsultationSkill
from app.ai.providers.base import AIResult, ConsultationContext, ConversationMessage
from app.ai.providers.mock import MockAIProvider
from app.ai.providers.openai import OpenAIProvider

DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"


class AIServiceError(RuntimeError):
    """Safe failure exposed to application callers."""


class AIConfigurationError(RuntimeError):
    """Safe startup failure for invalid server-side AI configuration."""


class AIService:
    def __init__(self, agent: ConsultationAgent) -> None:
        self._agent = agent

    def generate_response(
        self,
        context: ConsultationContext,
        messages: Sequence[ConversationMessage],
    ) -> AIResult:
        try:
            result = self._agent.respond(context, tuple(messages))
            return AIResult(result.content, result.structured_payload)
        except Exception:
            raise AIServiceError("Assistant response is temporarily unavailable") from None


def create_ai_service(environment: Mapping[str, str]) -> AIService:
    provider_name = environment.get("AI_PROVIDER", "openai").strip().lower()
    if provider_name == "mock":
        provider = MockAIProvider()
    elif provider_name == "openai":
        api_key = environment.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise AIConfigurationError("OPENAI_API_KEY is required for the OpenAI provider")
        model = environment.get("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip()
        if not model:
            raise AIConfigurationError("OPENAI_MODEL must not be blank")
        provider = OpenAIProvider(
            api_key=api_key,
            model=model,
            timeout_seconds=30.0,
            max_retries=1,
        )
    else:
        raise AIConfigurationError("Unsupported AI_PROVIDER configuration")

    return AIService(ConsultationAgent(provider, ConsultationSkill()))
