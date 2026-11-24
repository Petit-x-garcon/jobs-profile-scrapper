"""Store fractional years of experience."""

import sqlalchemy as sa

from alembic import op

revision = "0aed77c2bc41"
down_revision = "b72a0f6c91de"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Retain partial years in the profile."""
    op.alter_column("profiles", "years_experience", existing_type=sa.Integer(), type_=sa.Float())


def downgrade() -> None:
    """Restore whole-year storage, rounding partial years."""
    op.alter_column(
        "profiles",
        "years_experience",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        postgresql_using="round(years_experience)::integer",
    )
