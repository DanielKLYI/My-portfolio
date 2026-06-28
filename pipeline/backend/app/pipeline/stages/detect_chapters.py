"""Stage 2: Detect chapter boundaries."""
import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...models.db import PipelineStageRun
from ...services.pdf_parser import (
    PageContent, ChapterBoundary, detect_chapters_from_text
)
from ...services.extractor import _get_client
from ...config import settings
from .base import PipelineStage

FALLBACK_PROMPT = """Below are the first 3 pages of a nursing textbook.
Identify chapter boundaries and return a JSON array like:
[{{"chapter_number": 1, "title": "...", "page_start": 1, "page_end": 20}}, ...]
Return ONLY valid JSON.

Pages:
{text}
"""


class DetectChaptersStage(PipelineStage):
    name = "detect_chapters"

    async def run(self, textbook_id: str, db: AsyncSession) -> dict:
        # Load cached pages from parse stage
        cache_path = Path(settings.UPLOAD_DIR) / f"{textbook_id}_pages.json"
        cache_data = json.loads(cache_path.read_text())
        pages = [PageContent(**p) for p in cache_data["pages"]]
        total_pages = cache_data["total_pages"]

        # Use PDF bookmarks if available
        raw_bookmarks = cache_data.get("bookmarks", [])
        if raw_bookmarks:
            chapters = [ChapterBoundary(**b) for b in raw_bookmarks]
        else:
            chapters = detect_chapters_from_text(pages)

        # Fallback: ask Claude to parse the first few pages
        if not chapters:
            chapters = await _claude_detect(pages[:5], total_pages)

        # If we still have nothing, treat the whole book as one chapter
        if not chapters:
            chapters = [ChapterBoundary(
                chapter_number=1,
                title="Full Text",
                page_start=1,
                page_end=total_pages,
            )]

        chapter_dicts = [
            {
                "chapter_number": c.chapter_number,
                "title": c.title,
                "page_start": c.page_start,
                "page_end": c.page_end,
            }
            for c in chapters
        ]

        # Cache chapter boundaries for split stage
        chapters_path = Path(settings.UPLOAD_DIR) / f"{textbook_id}_chapters.json"
        chapters_path.write_text(json.dumps(chapter_dicts))

        return {"chapters_detected": len(chapters), "chapters_path": str(chapters_path)}


async def _claude_detect(pages: list[PageContent], total_pages: int) -> list[ChapterBoundary]:
    combined = "\n\n---PAGE BREAK---\n\n".join(
        f"[Page {p.number}]\n{p.text[:1000]}" for p in pages
    )
    client = _get_client()
    msg = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": FALLBACK_PROMPT.format(text=combined)}],
    )
    import re, json as _json
    raw = msg.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    data = _json.loads(raw)
    results = []
    for i, item in enumerate(data):
        page_end = data[i + 1]["page_start"] - 1 if i + 1 < len(data) else total_pages
        results.append(ChapterBoundary(
            chapter_number=item.get("chapter_number", i + 1),
            title=item["title"],
            page_start=item["page_start"],
            page_end=item.get("page_end", page_end),
        ))
    return results
