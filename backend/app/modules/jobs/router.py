import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.jobs import repository, service
from app.modules.jobs.schemas import ImportIn, JobOut, ScrapeIn, TaskOut
from app.shared.pagination import Page, PageQuery, SizeQuery

router = APIRouter(tags=["jobs"])


@router.get("/jobs")
async def list_jobs(
    page: PageQuery = 1,
    size: SizeQuery = 20,
    source: str | None = None,
    min_score: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> Page[JobOut]:
    """List jobs, best score first."""
    rows, total = await repository.list_jobs(page, size, source, min_score, db)
    return Page[JobOut](
        items=[JobOut.model_validate(r) for r in rows], total=total, page=page, size=size
    )


@router.get("/jobs/{job_id}")
async def get_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> JobOut:
    """Get one job."""
    return JobOut.model_validate(await service.get_job(job_id, db))


@router.post("/jobs/import", status_code=201)
async def import_job(data: ImportIn, db: AsyncSession = Depends(get_db)) -> JobOut:
    """Import a pasted job posting."""
    return JobOut.model_validate(await service.import_job(data, db))


@router.post("/scrape", status_code=202)
async def scrape(data: ScrapeIn) -> TaskOut:
    """Start a scrape in the background."""
    return TaskOut(task_id=service.enqueue_scrape(data.query))
