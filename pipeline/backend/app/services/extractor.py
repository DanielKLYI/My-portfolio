"""Entity extraction using Claude API."""
import json
import re
import anthropic
from ..config import settings

_client: anthropic.AsyncAnthropic | None = None

EXTRACTION_SCHEMA = {
    "diseases": "list of diseases, conditions, or disorders mentioned",
    "medications": "list of medications, drugs, or pharmacological agents",
    "labs": "list of laboratory tests, diagnostic values, or imaging studies",
    "interventions": "list of nursing interventions or actions",
    "nursing_diagnoses": "list of nursing diagnoses in NANDA format where applicable",
    "patient_education": "list of patient education topics or teaching points",
    "safety_concerns": "list of safety alerts, risks, or precautions",
    "clinical_judgment": "key clinical judgment and priority-setting points",
    "nclex_category": "single string: the primary NCLEX-PN/RN client needs category",
}

SYSTEM_PROMPT = """You are a nursing education expert and clinical content analyst.
Extract structured clinical information from nursing textbook chapters.
Return ONLY valid JSON — no prose, no markdown fences."""

EXTRACTION_PROMPT = """Extract the following from this nursing textbook chapter and return valid JSON with exactly these keys:

- diseases: array of strings
- medications: array of strings
- labs: array of strings
- interventions: array of strings
- nursing_diagnoses: array of strings (NANDA format where applicable)
- patient_education: array of strings
- safety_concerns: array of strings
- clinical_judgment: array of strings
- nclex_category: single string (e.g. "Physiological Integrity: Pharmacological and Parenteral Therapies")

Chapter title: {title}

Content (may be truncated):
{content}
"""


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


async def extract_entities(chapter_title: str, content_markdown: str) -> dict:
    """Call Claude to extract structured entities from a chapter."""
    truncated = content_markdown[: settings.EXTRACT_CHUNK_CHARS]
    prompt = EXTRACTION_PROMPT.format(title=chapter_title, content=truncated)

    client = _get_client()
    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    # Strip any accidental markdown fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)
