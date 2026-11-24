from pydantic import BaseModel, Field, field_validator

from app.modules.profile.schemas import Contact, EducationEntry, WorkEntry


class Enrichment(BaseModel):
    """AI output for one job."""

    summary: str
    score: int
    reasons: str
    matching_skills: list[str] = []
    missing_skills: list[str] = []

    @field_validator("score", mode="before")
    @classmethod
    def clamp_score(cls, v: object) -> int:
        """Clamp the score into 0-100."""
        return max(0, min(100, round(float(v))))  # type: ignore[arg-type]


class CVExtraction(BaseModel):
    """Profile data the AI extracted from a CV."""

    headline: str
    contact: Contact = Contact()
    summary: str
    skills: list[str] = []
    years_experience: float = Field(default=0, allow_inf_nan=False)
    experience: list[str | WorkEntry] = []
    education: list[str | EducationEntry] = []
    projects: list[str] = []
    certifications: list[str] = []
    awards: list[str] = []

    @field_validator("years_experience", mode="before")
    @classmethod
    def non_negative(cls, v: object) -> float:
        """Keep fractional years and prevent negative totals."""
        return max(0.0, round(float(v or 0), 2))  # type: ignore[arg-type]
