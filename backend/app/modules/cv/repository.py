from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cv.models import CV


async def get_active(db: AsyncSession) -> CV | None:
    """Return the current CV, if one was uploaded."""
    return await db.scalar(select(CV).order_by(CV.uploaded_at.desc()).limit(1))


async def replace(cv: CV, db: AsyncSession) -> CV:
    """Delete every stored CV and add this one. The caller commits."""
    await db.execute(delete(CV))
    db.add(cv)
    await db.flush()
    return cv
