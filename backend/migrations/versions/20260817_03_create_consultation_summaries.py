"""Create consultation summary and recommendation persistence.

Revision ID: 20260817_03
Revises: 20260813_02
Create Date: 2026-08-17 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260817_03"
down_revision = "20260813_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "consultation_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "consultation_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("patient_summary", sa.Text(), nullable=False),
        sa.Column("recommendation_rationale", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "btrim(patient_summary) <> ''",
            name="ck_consultation_summaries_patient_summary_nonblank",
        ),
        sa.CheckConstraint(
            "recommendation_rationale IS NULL "
            "OR btrim(recommendation_rationale) <> ''",
            name="ck_consultation_summaries_rationale_nonblank",
        ),
        sa.ForeignKeyConstraint(["consultation_id"], ["consultations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "consultation_id",
            name="uq_consultation_summaries_consultation_id",
        ),
    )
    op.create_table(
        "consultation_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("summary_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("treatment", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "position >= 1",
            name="ck_consultation_recommendations_position_positive",
        ),
        sa.CheckConstraint(
            "btrim(treatment) <> ''",
            name="ck_consultation_recommendations_treatment_nonblank",
        ),
        sa.ForeignKeyConstraint(
            ["summary_id"], ["consultation_summaries.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "summary_id",
            "position",
            name="uq_consultation_recommendations_summary_position",
        ),
    )


def downgrade() -> None:
    op.drop_table("consultation_recommendations")
    op.drop_table("consultation_summaries")
