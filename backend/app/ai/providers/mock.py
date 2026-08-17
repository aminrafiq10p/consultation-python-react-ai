"""Deterministic, network-free provider for architecture and tests."""

from app.ai.providers.base import (
    AIResult,
    ProviderRequest,
    SummaryProviderRequest,
    SummaryResult,
)


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

    def generate_summary(self, request: SummaryProviderRequest) -> SummaryResult:
        user_reports = [
            message.content for message in request.messages if message.role == "USER"
        ]
        reported_context = (
            "; ".join(user_reports) or request.consultation_context.primary_concern
        )
        return SummaryResult(
            patient_summary=f"The patient reported: {reported_context}",
            recommended_treatments=(
                "Discuss appropriate next steps with a qualified healthcare professional.",
            ),
            recommendation_rationale=(
                "A professional can assess the reported concern and advise suitable care."
            ),
        )
