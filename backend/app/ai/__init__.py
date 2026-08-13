"""Provider-neutral AI consultation boundary."""

from app.ai.providers.base import AIResult, ConsultationContext, ConversationMessage
from app.ai.service import AIConfigurationError, AIService, AIServiceError, create_ai_service

__all__ = [
    "AIConfigurationError",
    "AIResult",
    "AIService",
    "AIServiceError",
    "ConsultationContext",
    "ConversationMessage",
    "create_ai_service",
]
