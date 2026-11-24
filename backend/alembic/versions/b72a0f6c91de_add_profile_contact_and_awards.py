"""Add CV contact details and awards to profiles."""

import sqlalchemy as sa

from alembic import op

revision = "b72a0f6c91de"
down_revision = "9c90b982d71e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the new profile fields with defaults for existing rows."""
    op.add_column("profiles", sa.Column("contact", sa.JSON(), server_default="{}", nullable=False))
    op.add_column("profiles", sa.Column("awards", sa.JSON(), server_default="[]", nullable=False))


def downgrade() -> None:
    """Remove the new profile fields."""
    op.drop_column("profiles", "awards")
    op.drop_column("profiles", "contact")
