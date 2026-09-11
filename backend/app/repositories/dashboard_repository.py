"""Read-only repository for authoritative dashboard projections."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Final
from uuid import UUID

from sqlalchemy import Date, cast, func, literal, select, union_all
from sqlalchemy.orm import Session

from app.infrastructure.consultation_models import (
    Appointment,
    Consultation,
    ConsultationStatus,
    ConsultationSummary,
    Message,
)

DEFAULT_ACTIVITY_LIMIT: Final = 10
MAX_PROJECTION_LIMIT: Final = 100
TREND_DAYS: Final = 30


@dataclass(frozen=True)
class DashboardCounts:
    """Persisted consultation and appointment row counts."""

    total_consultations: int
    booked_appointments: int


@dataclass(frozen=True)
class DashboardTrend:
    """A daily count based on an authoritative consultation timestamp."""

    day: date
    consultation_count: int


@dataclass(frozen=True)
class DashboardActivity:
    """A recent activity item derived from persisted consultation lineage."""

    activity_type: str
    consultation_id: UUID
    timestamp: datetime


@dataclass(frozen=True)
class DashboardPendingClinicalReview:
    """A pending consultation presented as pending clinical work."""

    consultation_id: UUID
    patient_name: str
    primary_concern: str
    recommended_procedure: str
    status: ConsultationStatus


class DashboardRepository:
    """Provides focused, read-only aggregate and dashboard projection reads."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_counts(self) -> DashboardCounts:
        """Count consultations and appointments independently in one statement."""
        total_consultations = select(func.count(Consultation.id)).scalar_subquery()
        booked_appointments = select(func.count(Appointment.id)).scalar_subquery()
        row = self._session.execute(
            select(
                total_consultations.label("total_consultations"),
                booked_appointments.label("booked_appointments"),
            )
        ).one()

        return DashboardCounts(
            total_consultations=int(row.total_consultations),
            booked_appointments=int(row.booked_appointments),
        )

    def get_consultation_trends(
        self, *, as_of: date | datetime | None = None
    ) -> list[DashboardTrend]:
        """Return populated UTC daily buckets for the rolling 30-day window.

        A consultation is bucketed by the earliest timestamp in its persisted
        message, summary, or appointment lineage. Consultations without any
        such timestamp are intentionally absent.
        """
        end_day = _utc_date(as_of)
        start_day = end_day - timedelta(days=TREND_DAYS - 1)
        end_exclusive = end_day + timedelta(days=1)

        lineage = _timestamp_lineage().cte("consultation_timestamp_lineage")
        bucket = cast(func.timezone("UTC", lineage.c.authoritative_timestamp), Date)
        rows = self._session.execute(
            select(bucket.label("day"), func.count().label("consultation_count"))
            .select_from(lineage)
            .where(
                bucket >= start_day,
                bucket < end_exclusive,
            )
            .group_by(bucket)
            .order_by(bucket.asc())
        ).all()
        return [
            DashboardTrend(day=row.day, consultation_count=int(row.consultation_count))
            for row in rows
        ]

    def get_recent_activity(
        self, *, limit: int = DEFAULT_ACTIVITY_LIMIT
    ) -> list[DashboardActivity]:
        """Return bounded activity derived only from persisted authoritative rows."""
        bounded_limit = _bounded_limit(limit)
        # A windowed query keeps this one statement and is explicit about the
        # stable first-message tie break.
        first_message_ranked = select(
            Message.consultation_id.label("consultation_id"),
            Message.created_at.label("timestamp"),
            Message.id.label("event_id"),
            func.row_number()
            .over(
                partition_by=Message.consultation_id,
                order_by=(Message.created_at.asc(), Message.id.asc()),
            )
            .label("message_rank"),
        ).subquery("first_message_ranked")
        first_messages = select(
            first_message_ranked.c.consultation_id,
            first_message_ranked.c.timestamp,
            first_message_ranked.c.event_id,
            literal("conversation_started").label("activity_type"),
        ).where(first_message_ranked.c.message_rank == 1)
        summaries = select(
            ConsultationSummary.consultation_id,
            ConsultationSummary.created_at.label("timestamp"),
            ConsultationSummary.id.label("event_id"),
            literal("consultation_completed").label("activity_type"),
        )
        appointments = select(
            Appointment.consultation_id,
            Appointment.created_at.label("timestamp"),
            Appointment.id.label("event_id"),
            literal("appointment_booked").label("activity_type"),
        )
        activities = union_all(first_messages, summaries, appointments).cte(
            "dashboard_activity"
        )
        rows = self._session.execute(
            select(
                activities.c.activity_type,
                activities.c.consultation_id,
                activities.c.timestamp,
            )
            .order_by(
                activities.c.timestamp.desc(),
                activities.c.consultation_id.asc(),
                activities.c.activity_type.asc(),
                activities.c.event_id.asc(),
            )
            .limit(bounded_limit)
        ).all()
        return [
            DashboardActivity(
                activity_type=row.activity_type,
                consultation_id=row.consultation_id,
                timestamp=row.timestamp,
            )
            for row in rows
        ]

    def get_pending_clinical_reviews(
        self, *, limit: int = DEFAULT_ACTIVITY_LIMIT
    ) -> list[DashboardPendingClinicalReview]:
        """Return existing PENDING consultations as a read-only projection."""
        bounded_limit = _bounded_limit(limit)
        rows = self._session.execute(
            select(
                Consultation.id,
                Consultation.patient_name,
                Consultation.primary_concern,
                Consultation.recommended_procedure,
                Consultation.status,
            )
            .where(Consultation.status == ConsultationStatus.PENDING)
            .order_by(Consultation.patient_name.asc(), Consultation.id.asc())
            .limit(bounded_limit)
        ).all()
        return [
            DashboardPendingClinicalReview(
                consultation_id=row.id,
                patient_name=row.patient_name,
                primary_concern=row.primary_concern,
                recommended_procedure=row.recommended_procedure,
                status=row.status,
            )
            for row in rows
        ]


def _timestamp_lineage():
    """Build the authoritative timestamp union without loading ORM rows."""
    lineage_rows = union_all(
        select(Message.consultation_id, Message.created_at.label("timestamp")),
        select(
            ConsultationSummary.consultation_id,
            ConsultationSummary.created_at.label("timestamp"),
        ),
        select(Appointment.consultation_id, Appointment.created_at.label("timestamp")),
    ).subquery("lineage_rows")
    return select(
        lineage_rows.c.consultation_id,
        func.min(lineage_rows.c.timestamp).label("authoritative_timestamp"),
    ).group_by(lineage_rows.c.consultation_id)


def _utc_date(value: date | datetime | None) -> date:
    if value is None:
        return datetime.now(timezone.utc).date()
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).date()
    return value


def _bounded_limit(value: int) -> int:
    if type(value) is not int or value < 1:
        raise ValueError("projection limit must be a positive integer")
    return min(value, MAX_PROJECTION_LIMIT)
