"""Repository access for persisted consultation messages."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.consultation_models import Message


class MessageRepository:
    """Provides focused persistence operations for consultation messages."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def persist_message(self, message: Message) -> Message:
        """Commit one message and return the database-confirmed row."""
        try:
            self._session.add(message)
            self._session.commit()
            self._session.refresh(message)
        except Exception:
            self._session.rollback()
            raise

        return message

    def list_messages(self, consultation_id: UUID) -> list[Message]:
        """Return one consultation's messages in stable chronological order."""
        statement = (
            select(Message)
            .where(Message.consultation_id == consultation_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
        )
        return list(self._session.scalars(statement).all())
