import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.profile.schemas import ProfileOut


class CVOut(BaseModel):
    """The active CV's metadata and extracted text (the file bytes are never returned)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    content_type: str
    size_bytes: int
    text: str
    uploaded_at: datetime


class CVUploadOut(BaseModel):
    """Result of an upload: the new CV and the profile rebuilt from it."""

    cv: CVOut
    profile: ProfileOut
