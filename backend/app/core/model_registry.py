"""Import every module's models so Alembic autogenerate sees them."""

from app.modules.cv import models as cv_models  # noqa: F401
from app.modules.jobs import models as jobs_models  # noqa: F401
from app.modules.profile import models as profile_models  # noqa: F401
from app.modules.site_check import models as site_check_models  # noqa: F401
