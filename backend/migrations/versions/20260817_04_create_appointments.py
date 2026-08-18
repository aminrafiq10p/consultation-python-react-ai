"""Create appointment persistence.

Revision ID: 20260817_04
Revises: 20260817_03
Create Date: 2026-08-17 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260817_04"
down_revision = "20260817_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "appointments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("consultation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recommendation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "char_length(location) <= 200",
            name="ck_appointments_location_max_length",
        ),
        sa.CheckConstraint(
            "btrim(location) <> ''", name="ck_appointments_location_nonblank"
        ),
        sa.ForeignKeyConstraint(["consultation_id"], ["consultations.id"]),
        sa.ForeignKeyConstraint(
            ["recommendation_id"], ["consultation_recommendations.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "consultation_id", name="uq_appointments_consultation_id"
        ),
    )
    op.create_index(
        "ix_appointments_recommendation_id",
        "appointments",
        ["recommendation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_appointments_recommendation_id", table_name="appointments")
    op.drop_table("appointments")
