"""Initial HACSA Axis schema."""

from alembic import op  # noqa: F401

from app.connections import Base, engine
from app import models  # noqa: F401

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=engine)


def downgrade() -> None:
    Base.metadata.drop_all(bind=engine)
