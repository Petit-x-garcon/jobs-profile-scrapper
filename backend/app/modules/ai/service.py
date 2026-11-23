import logging

from openai import AsyncAzureOpenAI
from pydantic import ValidationError

from app.core.config import settings
from app.modules.ai.schemas import Enrichment
from app.shared.exceptions import AppException

logger = logging.getLogger(__name__)

MAX_DESCRIPTION_CHARS = 6000
TIMEOUT_SECONDS = 60

SYSTEM_PROMPT = (
    "You help a job seeker triage postings. Given a job posting and the candidate profile, "
    'reply with JSON only: {"summary": "3-5 short bullet lines, one per line, starting with - ", '
    '"score": integer 0-100 for how well the job fits the candidate, '
    '"reasons": "1-2 sentences explaining the score"}.'
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


async def enrich(job_text: str, profile_text: str) -> Enrichment:
    """Summarise a job and score its fit against the profile with one chat call."""
    client = _client()
    user = f"PROFILE:\n{profile_text}\n\nJOB:\n{job_text[:MAX_DESCRIPTION_CHARS]}"
    resp = await client.chat.completions.create(
        model=settings.azure_openai_deployment,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}],
        response_format={"type": "json_object"},
    )
    try:
        return Enrichment.model_validate_json(resp.choices[0].message.content or "")
    except (ValidationError, ValueError, TypeError) as exc:
        logger.warning("Invalid AI response: %s", exc)
        raise AIBadResponse("AI returned an invalid response.") from exc
