from fastapi import APIRouter, Depends, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.cv import service
from app.modules.cv.schemas import CVOut, CVUploadOut

router = APIRouter(prefix="/cv", tags=["cv"])


@router.get("")
async def get_cv(db: AsyncSession = Depends(get_db)) -> CVOut | None:
    """The active CV, or null. Public, like the profile: this app is single-user."""
    return await service.get_cv(db)


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_cv(file: UploadFile, db: AsyncSession = Depends(get_db)) -> CVUploadOut:
    """Upload a PDF/DOCX CV; it replaces the previous CV and its profile data.

    400 for unsupported, empty, oversized or unreadable files; 502/503 if AI fails.
    """
    data = await file.read(service.MAX_CV_BYTES + 1)  # +1 so an oversize file is detectable
    return await service.upload_cv(file.filename or "", data, db)
