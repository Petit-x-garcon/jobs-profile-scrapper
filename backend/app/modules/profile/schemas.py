import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Contact(BaseModel):
    """Contact details displayed on a CV."""

    name: str = ""
    phone: str = ""
    email: str = ""
    city: str = ""
    linkedin: str = ""
    portfolio: str = ""


class WorkEntry(BaseModel):
    """A role and its dates as written on the CV."""

    company: str = ""
    title: str = ""
    dates: str = ""


class EducationEntry(BaseModel):
    """A credential and its graduation year."""

    degree: str = ""
    university: str = ""
    year: str = ""


class ProfileIn(BaseModel):
    """Editable profile fields."""

    headline: str
    contact: Contact = Contact()
    skills: list[str]
    years_experience: float = Field(ge=0, allow_inf_nan=False)
    locations: list[str]
    remote_ok: bool
    min_salary: int | None = None
    summary: str
    experience: list[str | WorkEntry] = []
    education: list[str | EducationEntry] = []
    projects: list[str] = []
    certifications: list[str] = []
    awards: list[str] = []


class ProfileOut(ProfileIn):
    """Profile as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    updated_at: datetime
