import logging

from openai import AsyncAzureOpenAI
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
    '"summary": "2-4 sentence professional summary", "skills": [short skill names], '
    '"years_experience": integer total years of professional experience, '
    '"experience": ["Role at Company (dates): one-line highlights"], '
    '"education": ["Degree, School (year)"], "projects": ["Name: one-line description"], '
    '"certifications": ["Name (issuer, year)"]}. Use [] for missing sections.'
)


class AIUnavailable(AppException):
    """Azure OpenAI is not configured."""

    status_code = 503


class AIBadResponse(AppException):
    """The model returned something unusable."""

    status_code = 502


def _client() -> AsyncAzureOpenAI:
    if not (
        settings.azure_openai_endpoint
        and settings.azure_openai_api_key
        and settings.azure_openai_deployment
    ):
        raise AIUnavailable("Azure OpenAI is not configured.")
    return AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        timeout=TIMEOUT_SECONDS,
    )


async def _chat_json[T: BaseModel](system: str, user: str, schema: type[T]) -> T:
    """One JSON-mode chat call, parsed into `schema`; raises AIBadResponse on bad output."""
    client = _client()
    resp = await client.chat.completions.create(
        model=settings.azure_openai_deployment,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        response_format={"type": "json_object"},
    )
    try:
        return schema.model_validate_json(resp.choices[0].message.content or "")
    except (ValidationError, ValueError, TypeError) as exc:
        logger.warning("Invalid AI response: %s", exc)
        raise AIBadResponse("AI returned an invalid response.") from exc


async def enrich(job_text: str, profile_text: str) -> Enrichment:
    """Summarise a job and score its fit against the profile with one chat call."""
    user = f"PROFILE:\n{profile_text}\n\nJOB:\n{job_text[:MAX_DESCRIPTION_CHARS]}"
    return await _chat_json(SYSTEM_PROMPT, user, Enrichment)


async def extract_profile(cv_text: str) -> CVExtraction:
    """Turn raw CV text into structured profile data with one chat call."""
    return await _chat_json(CV_PROMPT, cv_text[:MAX_CV_CHARS], CVExtraction)
