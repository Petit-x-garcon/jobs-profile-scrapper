from pydantic import BaseModel, field_validator


class Enrichment(BaseModel):
    """AI output for one job."""

    summary: str
    score: int
    reasons: str

    @field_validator("score", mode="before")
    @classmethod
    def clamp_score(cls, v: object) -> int:
        """Clamp the score into 0-100."""
        return max(0, min(100, round(float(v))))  # type: ignore[arg-type]
