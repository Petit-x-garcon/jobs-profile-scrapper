import asyncio
import logging
from collections.abc import Callable
from pathlib import PurePath

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai import service as ai
from app.modules.cv import repository
from app.modules.cv.extract import docx_text, pdf_text
from app.modules.cv.models import CV
from app.modules.cv.schemas import CVOut, CVUploadOut
from app.modules.profile import service as profile_service
from app.modules.profile.schemas import ProfileOut
from app.shared.exceptions import BadRequest

logger = logging.getLogger(__name__)

MAX_CV_BYTES = 5 * 1024 * 1024
MIN_TEXT_CHARS = 50
DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
# extension -> (magic bytes, stored content type, text extractor)
_KINDS: dict[str, tuple[bytes, str, Callable[[bytes], str]]] = {
    ".pdf": (b"%PDF-", "application/pdf", pdf_text),
    ".docx": (b"PK\x03\x04", DOCX_TYPE, docx_text),
}


def _check_file(filename: str, data: bytes) -> str:
    """Return the file extension, or raise BadRequest for a bad type, size or signature."""
    ext = PurePath(filename).suffix.lower()
    if ext not in _KINDS:
        raise BadRequest("Unsupported file type. Upload a PDF (.pdf) or Word (.docx) file.")
    if not data:
        raise BadRequest("The file is empty.")
    if len(data) > MAX_CV_BYTES:
        raise BadRequest("The file is larger than 5 MB.")
    if not data.startswith(_KINDS[ext][0]):
        raise BadRequest(f"This is not a valid {ext} file.")
    return ext


async def _extract_text(ext: str, data: bytes) -> str:
    try:
        text = await asyncio.to_thread(_KINDS[ext][2], data)
    except Exception as exc:  # parsers raise many types; all mean "unreadable"
        logger.warning("CV extraction failed (%s): %s", ext, type(exc).__name__)
        raise BadRequest(
            "Could not read this file. Make sure it is a valid PDF or DOCX "
            "and not password-protected."
        ) from exc
    if len(text.strip()) < MIN_TEXT_CHARS:
        raise BadRequest(
            "No readable text found. If this is a scanned PDF, export it with selectable text."
        )
    return text.strip()


async def get_cv(db: AsyncSession) -> CVOut | None:
    """Return the active CV, or None if none was uploaded."""
    cv = await repository.get_active(db)
    return CVOut.model_validate(cv) if cv else None


async def upload_cv(filename: str, data: bytes, db: AsyncSession) -> CVUploadOut:
    """Validate, extract and parse a CV, then replace the old CV and profile data together.

    Nothing is stored unless every step succeeds. Raises BadRequest for bad files and
    AIUnavailable / AIBadResponse when the profile cannot be extracted.
    """
    ext = _check_file(filename, data)
    text = await _extract_text(ext, data)
    extracted = await ai.extract_profile(text)
    cv = CV(
        filename=PurePath(filename).name[:255],
        content_type=_KINDS[ext][1],
        size_bytes=len(data),
        data=data,
        text=text,
    )
    await repository.replace(cv, db)
    profile = await profile_service.apply_cv(extracted, db)
    await db.commit()
    logger.info("Replaced active CV with %s", cv.id)
    return CVUploadOut(cv=CVOut.model_validate(cv), profile=ProfileOut.model_validate(profile))
