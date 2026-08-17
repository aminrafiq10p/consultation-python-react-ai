"""Repository access for persisted consultation summary aggregates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.infrastructure.consultation_models import (
    Consultation,
    ConsultationRecommendation,
    ConsultationStatus,
    ConsultationSummary,
)


SUMMARY_CONSULTATION_UNIQUE_CONSTRAINT = (
    "uq_consultation_summaries_consultation_id"
)


@dataclass(frozen=True)
class SummaryAggregate:
    """One persisted summary and its deterministically ordered children."""

    summary: ConsultationSummary
    recommendations: tuple[ConsultationRecommendation, ...]


@dataclass(frozen=True)
class SummaryCompletion:
    """Result of creating an aggregate or recovering a concurrent winner."""

    aggregate: SummaryAggregate
    created: bool


class SummaryRepository:
    """Owns retrieval and atomic persistence of summary aggregates."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_summary(self, consultation_id: UUID) -> SummaryAggregate | None:
        """Return one summary with children ordered by position and UUID."""
        summary = self._session.scalar(
            select(ConsultationSummary).where(
                ConsultationSummary.consultation_id == consultation_id
            )
        )
        if summary is None:
            return None

        recommendations = tuple(
            self._session.scalars(
                select(ConsultationRecommendation)
                .where(ConsultationRecommendation.summary_id == summary.id)
                .order_by(
                    ConsultationRecommendation.position.asc(),
                    ConsultationRecommendation.id.asc(),
                )
            ).all()
        )
        return SummaryAggregate(summary=summary, recommendations=recommendations)

    def complete_consultation(
        self,
        consultation: Consultation,
        *,
        patient_summary: str,
        recommended_treatments: Sequence[str],
        recommendation_rationale: str | None = None,
    ) -> SummaryCompletion:
        """Atomically persist the aggregate and consultation completion fields."""
        summary = ConsultationSummary(
            consultation_id=consultation.id,
            patient_summary=patient_summary,
            recommendation_rationale=recommendation_rationale,
        )

        try:
            self._session.add(summary)
            self._session.flush()
            recommendations = tuple(
                ConsultationRecommendation(
                    summary_id=summary.id,
                    treatment=treatment,
                    position=position,
                )
                for position, treatment in enumerate(recommended_treatments, start=1)
            )
            self._session.add_all(recommendations)

            # Validation of the provider-neutral result belongs to the application
            # boundary. Indexing here also prevents an empty aggregate from being
            # committed if that defensive invariant is ever missed there.
            consultation.recommended_procedure = recommendations[0].treatment
            consultation.status = ConsultationStatus.COMPLETED

            self._session.commit()
            aggregate = self.get_summary(consultation.id)
            if aggregate is None:  # pragma: no cover - defensive post-commit guard
                raise RuntimeError("committed summary aggregate could not be reloaded")
            return SummaryCompletion(aggregate=aggregate, created=True)
        except IntegrityError as error:
            self._session.rollback()
            if self._constraint_name(error) != SUMMARY_CONSULTATION_UNIQUE_CONSTRAINT:
                raise

            winner = self.get_summary(consultation.id)
            if winner is None:
                raise
            return SummaryCompletion(aggregate=winner, created=False)
        except Exception:
            self._session.rollback()
            raise

    @staticmethod
    def _constraint_name(error: IntegrityError) -> str | None:
        diagnostic = getattr(error.orig, "diag", None)
        return getattr(diagnostic, "constraint_name", None)
