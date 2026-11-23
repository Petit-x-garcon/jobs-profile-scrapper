from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.jobs import service as jobs_service
from app.modules.profile import repository
from app.modules.profile.models import Profile
from app.modules.profile.schemas import ProfileIn

# PLACEHOLDER sample; the user edits it via PUT /api/profile.
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
    """Update the profile, then reset job scores and queue re-scoring."""
    profile = await get_profile(db)
    for field, value in data.model_dump().items():
        setattr(profile, field, value)
    await repository.save(profile, db)
    await jobs_service.reset_and_rescore(db)
    return profile


def profile_text(profile: Profile) -> str:
    """Plain-text rendering of the profile for the AI prompt."""
    salary = f"\nMinimum salary: {profile.min_salary}" if profile.min_salary else ""
    return (
        f"{profile.headline}\nSkills: {', '.join(profile.skills)}\n"
        f"Experience: {profile.years_experience} years\n"
        f"Locations: {', '.join(profile.locations)}\nRemote OK: {profile.remote_ok}{salary}\n"
        f"{profile.summary}"
    )
