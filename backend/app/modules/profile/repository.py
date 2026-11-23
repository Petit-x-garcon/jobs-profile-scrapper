from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.profile.models import Profile


async def get(db: AsyncSession) -> Profile | None:
    """Return the single profile row, if any."""
    return await db.scalar(select(Profile).limit(1))


async def save(profile: Profile, db: AsyncSession) -> Profile:
    """Insert or update the profile."""
    db.add(profile)
    await db.commit()
    return profile
