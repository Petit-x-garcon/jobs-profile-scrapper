"""Add saved scrape sites."""

import sqlalchemy as sa

from alembic import op

revision = "9c90b982d71e"
down_revision = "534dbec22b7a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the saved scrape sites table."""
    op.create_table(
        "scrape_sites",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("url", sa.String(length=2048), nullable=False, unique=True),
    )


def downgrade() -> None:
    """Drop the saved scrape sites table."""
    op.drop_table("scrape_sites")
