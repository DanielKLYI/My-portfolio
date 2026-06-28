"""Stage 1: Parse PDF into pages and detect bookmarks."""
import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...models.db import Textbook
from ...services.pdf_parser import parse_pdf, ParsedPDF, PageContent, ChapterBoundary
from ...config import settings
from .base import PipelineStage


class ParseStage(PipelineStage):
    name = "parse"

    async def run(self, textbook_id: str, db: AsyncSession) -> dict:
        result = await db.execute(select(Textbook).where(Textbook.id == textbook_id))
        book = result.scalar_one()

        parsed = parse_pdf(book.file_path)

        # Persist pages as JSON for downstream stages
        cache_path = Path(settings.UPLOAD_DIR) / f"{textbook_id}_pages.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_data = {
            "total_pages": parsed.total_pages,
            "pages": [
                {"number": p.number, "text": p.text, "headings": p.headings}
                for p in parsed.pages
            ],
            "bookmarks": [
                {
                    "chapter_number": b.chapter_number,
                    "title": b.title,
                    "page_start": b.page_start,
                    "page_end": b.page_end,
                }
                for b in parsed.bookmarks
            ],
        }
        cache_path.write_text(json.dumps(cache_data))

        return {
            "total_pages": parsed.total_pages,
            "bookmarks_found": len(parsed.bookmarks),
            "cache_path": str(cache_path),
        }
