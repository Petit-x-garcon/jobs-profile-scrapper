"""Import every module's models so Alembic autogenerate sees them."""

from app.modules.jobs import models as jobs_models  # noqa: F401
from app.modules.profile import models as profile_models  # noqa: F401
