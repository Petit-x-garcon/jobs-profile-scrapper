from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.schemas import CVExtraction
from app.modules.jobs import service as jobs_service
from app.modules.profile import repository
from app.modules.profile.models import Profile
from app.modules.profile.schemas import ProfileIn

# PLACEHOLDER sample; the user edits it via PUT /api/profile or a CV upload.
SEED = ProfileIn(
    headline="Full-stack Developer (sample — edit me)",
    skills=["Python", "FastAPI", "PostgreSQL", "Next.js", "React", "TypeScript", "Docker"],
    years_experience=2,
    locations=["Phnom Penh"],
    remote_ok=True,
    min_salary=None,
    summary="Sample profile. Replace with your real experience.",
)


async def get_profile(db: AsyncSession) -> Profile:
    """Return the profile, creating the placeholder seed if missing."""
    return await repository.get(db) or await repository.save(Profile(**SEED.model_dump()), db)


async def update_profile(data: ProfileIn, db: AsyncSession) -> Profile:
    """Replace the profile and clear job scores so the next analysis uses it."""
    profile = await get_profile(db)
    omitted = {"contact", "awards"} - data.model_fields_set
    for field, value in data.model_dump(exclude=omitted).items():
        setattr(profile, field, value)
    await jobs_service.reset_scores(db)
    return await repository.save(profile, db)


async def apply_cv(data: CVExtraction, db: AsyncSession) -> Profile:
    """Overwrite the CV-derived fields (search preferences are kept). The caller commits."""
    profile = await get_profile(db)
    for field, value in data.model_dump().items():
        setattr(profile, field, value)
    await jobs_service.reset_scores(db)
    return profile


def _section(title: str, items: list[str | dict[str, str]] | list[str]) -> str:
    lines = [
        item if isinstance(item, str) else " · ".join(filter(None, item.values())) for item in items
    ]
    return f"\n{title}:\n" + "\n".join(f"- {line}" for line in lines) if lines else ""


def profile_text(profile: Profile) -> str:
    """Plain-text rendering of the profile for the AI prompt."""
    salary = f"\nMinimum salary: {profile.min_salary}" if profile.min_salary else ""
    return (
        f"{profile.headline}\nSkills: {', '.join(profile.skills)}\n"
        f"Experience: {profile.years_experience:g} years\n"
        f"Locations: {', '.join(profile.locations)}\nRemote OK: {profile.remote_ok}{salary}\n"
        f"{profile.summary}"
        + _section("Work experience", profile.experience)
        + _section("Education", profile.education)
        + _section("Projects", profile.projects)
        + _section("Certifications", profile.certifications)
        + _section("Awards", profile.awards)
    )
