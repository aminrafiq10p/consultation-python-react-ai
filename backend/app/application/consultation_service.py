"""Application services for consultation records and persisted conversation."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from app.ai import (
    AIResult,
    AIService,
    ConsultationContext,
    ConversationMessage,
    SummaryResult,
)

from app.infrastructure.consultation_models import (
    Consultation,
    ConsultationStatus,
    Message,
    MessageRole,
)
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.summary_repository import SummaryAggregate, SummaryRepository

MAX_MESSAGE_LENGTH = 4_000
MAX_CONTEXT_MESSAGES = 20
MAX_CONTEXT_CHARACTERS = 24_000


class ConsultationNotFoundError(Exception):
    """Raised when a requested consultation does not exist."""


class InvalidMessageError(ValueError):
    """Raised when submitted message content violates application invariants."""


class AIGenerationError(RuntimeError):
    """Recoverable AI failure after a user message has been persisted."""

    def __init__(self, user_message: Message) -> None:
        super().__init__("Assistant response is temporarily unavailable")
        self.user_message = user_message


class SummaryNotAvailableError(RuntimeError):
    """Raised when a consultation has no persisted summary to retrieve."""


class SummaryNotEligibleError(RuntimeError):
    """Raised when a consultation cannot begin initial summary generation."""


class SummaryGenerationError(RuntimeError):
    """Safe outcome for failed or malformed AI summary generation."""


class ConsultationConversationClosedError(RuntimeError):
    """Raised when a non-pending consultation receives a new message."""


class ConsultationNotRestartableError(RuntimeError):
    """Raised when a consultation is not a completed summarized source."""


@dataclass(frozen=True)
class PersistedExchange:
    """The database-confirmed messages produced by one successful submission."""

    user_message: Message
    assistant_message: Message


@dataclass(frozen=True)
class GeneratedSummary:
    """Persisted summary plus whether this request committed it."""

    aggregate: SummaryAggregate
    created: bool


def select_conversation_context(
    history: list[Message],
    current_user_message: Message,
) -> list[Message]:
    """Select the bounded newest persisted tail, retaining the current user."""
    selected_reversed = [current_user_message]
    selected_characters = len(current_user_message.content)
    current_id = current_user_message.id

    for message in reversed(history):
        if message.id == current_id:
            continue
        if len(selected_reversed) >= MAX_CONTEXT_MESSAGES:
            break
        message_characters = len(message.content)
        if selected_characters + message_characters > MAX_CONTEXT_CHARACTERS:
            break
        selected_reversed.append(message)
        selected_characters += message_characters

    return list(reversed(selected_reversed))


class ConsultationApplicationService:
    """Coordinates consultation-record use cases."""

    def __init__(
        self,
        repository: ConsultationRepository,
        message_repository: MessageRepository | None = None,
        ai_service: AIService | None = None,
        summary_repository: SummaryRepository | None = None,
    ) -> None:
        self._repository = repository
        self._message_repository = message_repository
        self._ai_service = ai_service
        self._summary_repository = summary_repository

    def list_consultations(
        self,
        *,
        search: str | None = None,
        status: ConsultationStatus | None = None,
    ) -> list[Consultation]:
        """Return consultation records using the validated filters unchanged."""
        return self._repository.get_consultations(
            search=search,
            status=status,
        )

    def get_consultation(
        self,
        consultation_id: UUID,
    ) -> Consultation:
        """Return one consultation or raise the application not-found outcome."""
        consultation = self._repository.get_consultation_by_id(
            consultation_id,
        )

        if consultation is None:
            raise ConsultationNotFoundError

        return consultation

    def get_messages(self, consultation_id: UUID) -> list[Message]:
        """Return repository-ordered persisted history for a consultation."""
        self.get_consultation(consultation_id)
        if self._message_repository is None:
            raise RuntimeError("Message repository is not configured")
        return self._message_repository.list_messages(consultation_id)

    def submit_message(
        self,
        consultation_id: UUID,
        content: str,
    ) -> PersistedExchange:
        """Persist a user message, generate a response, and persist that response."""
        normalized_content = self._normalize_message_content(content)
        consultation = self.get_consultation(consultation_id)
        if consultation.status is not ConsultationStatus.PENDING:
            raise ConsultationConversationClosedError
        message_repository, ai_service = self._conversation_dependencies()

        persisted_user = message_repository.persist_message(
            Message(
                consultation_id=consultation_id,
                role=MessageRole.USER,
                content=normalized_content,
                structured_payload=None,
            )
        )
        history = message_repository.list_messages(consultation_id)
        selected_history = select_conversation_context(history, persisted_user)

        try:
            raw_result = ai_service.generate_response(
                ConsultationContext(
                    consultation_id=str(consultation.id),
                    primary_concern=consultation.primary_concern,
                    display_fields={
                        "patient_name": consultation.patient_name,
                        "recommended_procedure": consultation.recommended_procedure,
                        "status": consultation.status.value,
                    },
                ),
                [
                    ConversationMessage(
                        role=message.role.value,
                        content=message.content,
                    )
                    for message in selected_history
                ],
            )
            result = AIResult(
                content=raw_result.content,
                structured_payload=raw_result.structured_payload,
            )
        except Exception:
            raise AIGenerationError(persisted_user) from None

        persisted_assistant = message_repository.persist_message(
            Message(
                consultation_id=consultation_id,
                role=MessageRole.ASSISTANT,
                content=result.content,
                structured_payload=result.structured_payload,
            )
        )
        return PersistedExchange(
            user_message=persisted_user,
            assistant_message=persisted_assistant,
        )

    def get_summary(self, consultation_id: UUID) -> SummaryAggregate:
        """Return a persisted summary without invoking AI."""
        self.get_consultation(consultation_id)
        summary_repository = self._summary_dependency()
        aggregate = summary_repository.get_summary(consultation_id)
        if aggregate is None:
            raise SummaryNotAvailableError
        return aggregate

    def generate_summary(self, consultation_id: UUID) -> GeneratedSummary:
        """Idempotently generate and atomically persist an eligible summary."""
        consultation = self.get_consultation(consultation_id)
        summary_repository = self._summary_dependency()

        existing = summary_repository.get_summary(consultation_id)
        if existing is not None:
            return GeneratedSummary(aggregate=existing, created=False)

        if consultation.status is not ConsultationStatus.PENDING:
            raise SummaryNotEligibleError

        message_repository, ai_service = self._conversation_dependencies()
        history = message_repository.list_messages(consultation_id)
        roles = {message.role for message in history}
        if (
            MessageRole.USER not in roles
            or MessageRole.ASSISTANT not in roles
            or history[-1].role is not MessageRole.ASSISTANT
        ):
            raise SummaryNotEligibleError

        try:
            raw_result = ai_service.generate_summary(
                self._consultation_context(consultation),
                tuple(
                    ConversationMessage(
                        role=message.role.value,
                        content=message.content,
                    )
                    for message in history
                ),
            )
            result = SummaryResult(
                patient_summary=raw_result.patient_summary,
                recommended_treatments=raw_result.recommended_treatments,
                recommendation_rationale=raw_result.recommendation_rationale,
            )
        except Exception:
            raise SummaryGenerationError(
                "Consultation summary is temporarily unavailable"
            ) from None

        completion = summary_repository.complete_consultation(
            consultation,
            patient_summary=result.patient_summary,
            recommended_treatments=result.recommended_treatments,
            recommendation_rationale=result.recommendation_rationale,
        )
        return GeneratedSummary(
            aggregate=completion.aggregate,
            created=completion.created,
        )

    def restart_consultation(self, consultation_id: UUID) -> Consultation:
        """Create a fresh pending consultation from a completed summary source."""
        source = self.get_consultation(consultation_id)
        summary_repository = self._summary_dependency()
        if (
            source.status is not ConsultationStatus.COMPLETED
            or summary_repository.get_summary(consultation_id) is None
        ):
            raise ConsultationNotRestartableError

        return self._repository.create_consultation(
            Consultation(
                id=uuid4(),
                patient_name=source.patient_name,
                primary_concern=source.primary_concern,
                recommended_procedure="",
                status=ConsultationStatus.PENDING,
            )
        )

    @staticmethod
    def _normalize_message_content(content: str) -> str:
        if not isinstance(content, str):
            raise InvalidMessageError("Message content must be text")
        normalized = content.strip()
        if not normalized:
            raise InvalidMessageError("Message content must not be blank")
        if len(normalized) > MAX_MESSAGE_LENGTH:
            raise InvalidMessageError("Message content exceeds 4,000 characters")
        return normalized

    def _conversation_dependencies(self) -> tuple[MessageRepository, AIService]:
        if self._message_repository is None or self._ai_service is None:
            raise RuntimeError("Conversation dependencies are not configured")
        return self._message_repository, self._ai_service

    def _summary_dependency(self) -> SummaryRepository:
        if self._summary_repository is None:
            raise RuntimeError("Summary repository is not configured")
        return self._summary_repository

    @staticmethod
    def _consultation_context(consultation: Consultation) -> ConsultationContext:
        return ConsultationContext(
            consultation_id=str(consultation.id),
            primary_concern=consultation.primary_concern,
            display_fields={
                "patient_name": consultation.patient_name,
                "recommended_procedure": consultation.recommended_procedure,
                "status": consultation.status.value,
            },
        )
