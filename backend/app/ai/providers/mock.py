"""Deterministic, network-free provider for architecture and tests."""

from app.ai.providers.base import AIResult, ProviderRequest


class MockAIProvider:
    def generate(self, request: ProviderRequest) -> AIResult:
        latest_user_content = next(
            (message.content for message in reversed(request.messages) if message.role == "USER"),
            request.consultation_context.primary_concern,
        )
        return AIResult(
            content=f"I understand your concern: {latest_user_content}",
            structured_payload={"provider": "mock", "message_count": len(request.messages)},
        )
