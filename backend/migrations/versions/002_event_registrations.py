"""Add persistent event registrations."""

from alembic import op
import sqlalchemy as sa

revision = "002_event_registrations"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_registrations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("event_name", sa.String(length=250), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("registered_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "user_id", name="uq_event_registration_user"),
    )
    op.create_index("ix_event_registration_event", "event_registrations", ["event_id"])
    op.create_index("ix_event_registrations_id", "event_registrations", ["id"])


def downgrade() -> None:
    op.drop_index("ix_event_registrations_id", table_name="event_registrations")
    op.drop_index("ix_event_registration_event", table_name="event_registrations")
    op.drop_table("event_registrations")
