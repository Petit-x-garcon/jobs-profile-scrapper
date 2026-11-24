from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.recommendations import service
from app.modules.recommendations.schemas import AnalyzeIn, RecommendationsOut

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("")
async def analyze(data: AnalyzeIn, db: AsyncSession = Depends(get_db)) -> RecommendationsOut:
    """Analyze the given jobs against the latest profile with AI (public, single-user app).

    503 if AI is not configured, 404 if none of the jobs exist.
    """
    return await service.analyze(data.job_ids, db)
