import logging

from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.modules.ai.schemas import CVExtraction, Enrichment
from app.shared.exceptions import AppException

logger = logging.getLogger(__name__)

MAX_DESCRIPTION_CHARS = 6000
TIMEOUT_SECONDS = 60

MAX_CV_CHARS = 20000

SYSTEM_PROMPT = (
    "You help a job seeker triage postings. Given a job posting and the candidate profile, "
    'reply with JSON only: {"summary": "3-5 short bullet lines, one per line, starting with - ", '
    '"score": integer 0-100 for how well the job fits the candidate\'s experience, skills '
    "and qualifications, "
    '"reasons": "1-3 sentences explaining why the job is or is not suitable", '
    '"matching_skills": [skills/qualifications the job asks for that the candidate has], '
    '"missing_skills": [skills/requirements the job asks for that the candidate lacks]}.'
)

CV_PROMPT = (
    "Extract the candidate's profile from this CV text. Use only facts in the CV. "
    'Reply with JSON only: {"headline": "current or target role, short", '
    '"contact": {"name": "", "phone": "", "email": "", "city": "", "linkedin": "", '
    '"portfolio": ""}, '
    '"summary": "2-4 sentence professional summary", "skills": [short skill names], '
    '"years_experience": number of years in professional jobs, including partial years, '
    '"experience": [{"company": "", "title": "", "dates": ""}], '
    '"education": [{"degree": "", "university": "", "year": ""}], '
    '"projects": ["Name: one-line description"], "certifications": ["Name (issuer, year)"], '
    '"awards": ["Name (issuer, year)"]}. Use [] for missing sections and empty strings '
    "for missing contact or entry details. "
    "Extract every work entry, including internships, in newest-first order. Keep internships "
    "identifiable in their titles. Include all education entries, even ongoing studies or "
    "entries without a graduation year. Keep the degree or field of study and school when present. "
    "For years_experience, sum the months in non-internship jobs without double-counting "
    "overlapping periods and divide by 12. Use a stated role duration when its dates are missing "
    "or placeholders. For example, nine months of employment is 0.75 years. Use zero only when no "
    "non-internship duration is known."
)


class AIUnavailable(AppException):
    """Azure OpenAI is not configured."""

    status_code = 503


class AIBadResponse(AppException):
    """The model returned something unusable."""

    status_code = 502


def _client() -> AsyncOpenAI:
    endpoint = settings.azure_openai_endpoint
    if not (endpoint and settings.azure_openai_api_key and settings.azure_openai_deployment):
        raise AIUnavailable("Azure OpenAI is not configured.")
    base_url = endpoint.rstrip("/")
    if not base_url.endswith("/openai/v1"):
        base_url += "/openai/v1"
    return AsyncOpenAI(
        base_url=base_url,
        api_key=settings.azure_openai_api_key,
        timeout=TIMEOUT_SECONDS,
    )


async def _request_json[T: BaseModel](system: str, user: str, schema: type[T]) -> T:
    """Request JSON from Azure and validate it against the supplied schema."""
    async with _client() as client:
        resp = await client.responses.create(
            model=settings.azure_openai_deployment,
            input=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            text={"format": {"type": "json_object"}},
            store=False,
        )
    try:
        return schema.model_validate_json(resp.output_text)
    except ValidationError as exc:
        logger.warning("Invalid AI response for schema %s", schema.__name__)
        raise AIBadResponse("AI returned an invalid response.") from exc


async def enrich(job_text: str, profile_text: str) -> Enrichment:
    """Summarise a job and score its fit against the profile with one AI request."""
    user = f"PROFILE:\n{profile_text}\n\nJOB:\n{job_text[:MAX_DESCRIPTION_CHARS]}"
    return await _request_json(SYSTEM_PROMPT, user, Enrichment)


async def extract_profile(cv_text: str) -> CVExtraction:
    """Turn raw CV text into structured profile data with one chat call."""
    return await _request_json(CV_PROMPT, cv_text[:MAX_CV_CHARS], CVExtraction)
