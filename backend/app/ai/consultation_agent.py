"""The single agent that coordinates consultation instructions and a provider."""

from collections.abc import Sequence

from app.ai.consultation_skill import ConsultationSkill
from app.ai.providers.base import (
    AIProvider,
    AIResult,
    ConsultationContext,
    ConversationMessage,
    ProviderRequest,
)


class ConsultationAgent:
    def __init__(self, provider: AIProvider, skill: ConsultationSkill | None = None) -> None:
        self._provider = provider
        self._skill = skill or ConsultationSkill()

    def respond(
        self,
        context: ConsultationContext,
        messages: Sequence[ConversationMessage],
    ) -> AIResult:
        ordered_messages = tuple(messages)
        request = ProviderRequest(
            system_instruction=self._skill.instructions_for(context),
            consultation_context=context,
            messages=ordered_messages,
        )
        return self._provider.generate(request)
