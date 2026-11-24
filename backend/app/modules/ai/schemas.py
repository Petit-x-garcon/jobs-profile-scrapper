from pydantic import BaseModel, field_validator


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
    summary: str
    skills: list[str] = []
    years_experience: int = 0
    experience: list[str] = []
    education: list[str] = []
    projects: list[str] = []
    certifications: list[str] = []

    @field_validator("years_experience", mode="before")
    @classmethod
    def non_negative(cls, v: object) -> int:
        """Coerce to a non-negative whole number of years."""
        return max(0, round(float(v or 0)))  # type: ignore[arg-type]
