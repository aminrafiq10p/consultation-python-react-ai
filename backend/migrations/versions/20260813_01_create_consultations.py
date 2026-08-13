"""Create consultation persistence.

Revision ID: 20260813_01
Revises:
Create Date: 2026-08-13 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260813_01"
down_revision = None
branch_labels = None
depends_on = None


consultation_status = postgresql.ENUM(
    "PENDING",
    "BOOKED",
    "COMPLETED",
    name="consultation_status",
    create_type=False,
)


def upgrade() -> None:
    consultation_status.create(op.get_bind(), checkfirst=False)
    op.create_table(
        "consultations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_name", sa.Text(), nullable=False),
        sa.Column("primary_concern", sa.Text(), nullable=False),
        sa.Column("recommended_procedure", sa.Text(), nullable=False),
        sa.Column("status", consultation_status, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("consultations")
    consultation_status.drop(op.get_bind(), checkfirst=False)
