from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.recommendations import service
from app.modules.recommendations.schemas import (
    AnalyzeIn,
    LocalMatch,
    RankingQuery,
    RecommendationsOut,
    ShortlistItem,
    ShortlistQuery,
)
from app.shared.pagination import Page

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("")
async def analyze(data: AnalyzeIn, db: AsyncSession = Depends(get_db)) -> RecommendationsOut:
    """Analyze the given jobs against the latest profile with AI (public, single-user app).

    503 if AI is not configured, 404 if none of the jobs exist.
    """
    return await service.analyze(data.job_ids, db)


@router.get("/rankings")
async def shortlist(
    filters: Annotated[RankingQuery, Query()], db: AsyncSession = Depends(get_db)
) -> Page[LocalMatch]:
    """Page through the full local ranking without contacting the AI provider."""
    return await service.shortlist(filters, db)


@router.get("/shortlist", deprecated=True)
async def legacy_shortlist(
    filters: Annotated[ShortlistQuery, Query()], db: AsyncSession = Depends(get_db)
) -> list[ShortlistItem] | Page[LocalMatch]:
    """Preserve the response shape requested by previously loaded clients."""
    return await service.legacy_shortlist(filters, db)
