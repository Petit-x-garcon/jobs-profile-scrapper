from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.profile import service
from app.modules.profile.schemas import ProfileIn, ProfileOut

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("")
async def get_profile(db: AsyncSession = Depends(get_db)) -> ProfileOut:
    """Get the profile (seeded on first call)."""
    return ProfileOut.model_validate(await service.get_profile(db))


@router.put("")
async def put_profile(data: ProfileIn, db: AsyncSession = Depends(get_db)) -> ProfileOut:
    """Replace the profile and trigger re-scoring."""
    return ProfileOut.model_validate(await service.update_profile(data, db))
