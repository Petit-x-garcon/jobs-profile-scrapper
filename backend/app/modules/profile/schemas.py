import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProfileIn(BaseModel):
    """Editable profile fields."""

    headline: str
    skills: list[str]
    years_experience: int
    locations: list[str]
    remote_ok: bool
    min_salary: int | None = None
    summary: str


class ProfileOut(ProfileIn):
    """Profile as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    updated_at: datetime
