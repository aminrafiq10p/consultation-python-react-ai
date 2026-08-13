"""Create consultation message persistence.

Revision ID: 20260813_02
Revises: 20260813_01
Create Date: 2026-08-13 00:01:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260813_02"
down_revision = "20260813_01"
branch_labels = None
depends_on = None


message_role = postgresql.ENUM(
    "USER",
    "ASSISTANT",
    name="message_role",
    create_type=False,
)


def upgrade() -> None:
    message_role.create(op.get_bind(), checkfirst=False)
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("consultation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", message_role, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("structured_payload", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role != 'USER' OR structured_payload IS NULL",
            name="ck_messages_user_structured_payload_null",
        ),
        sa.ForeignKeyConstraint(["consultation_id"], ["consultations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_messages_consultation_id_created_at_id",
        "messages",
        ["consultation_id", "created_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_messages_consultation_id_created_at_id", table_name="messages"
    )
    op.drop_table("messages")
    message_role.drop(op.get_bind(), checkfirst=False)
