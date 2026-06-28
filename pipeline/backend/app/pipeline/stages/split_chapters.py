"""Stage 3: Create Chapter records with markdown content."""
import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from ...models.db import Chapter, Textbook
from ...services.pdf_parser import PageContent, pages_to_markdown
from ...config import settings
from .base import PipelineStage


class SplitChaptersStage(PipelineStage):
    name = "split_chapters"

    async def run(self, textbook_id: str, db: AsyncSession) -> dict:
        pages_cache = Path(settings.UPLOAD_DIR) / f"{textbook_id}_pages.json"
        chapters_cache = Path(settings.UPLOAD_DIR) / f"{textbook_id}_chapters.json"

        pages = [PageContent(**p) for p in json.loads(pages_cache.read_text())["pages"]]
        chapter_defs = json.loads(chapters_cache.read_text())

        # Remove any previously created chapters so re-runs are idempotent
        await db.execute(delete(Chapter).where(Chapter.textbook_id == textbook_id))

        md_dir = Path(settings.MARKDOWN_DIR) / textbook_id
        md_dir.mkdir(parents=True, exist_ok=True)

        for ch in chapter_defs:
            markdown = pages_to_markdown(pages, ch["page_start"], ch["page_end"])
            # Save markdown file
            md_file = md_dir / f"chapter_{ch['chapter_number']:03d}.md"
            md_file.write_text(f"# {ch['title']}\n\n{markdown}")

            chapter = Chapter(
                textbook_id=textbook_id,
                chapter_number=ch["chapter_number"],
                title=ch["title"],
                content_markdown=markdown,
                page_start=ch["page_start"],
                page_end=ch["page_end"],
            )
            db.add(chapter)

        # Update textbook chapter count
        result = await db.execute(select(Textbook).where(Textbook.id == textbook_id))
        book = result.scalar_one()
        book.total_chapters = len(chapter_defs)
        book.processed_chapters = 0

        await db.flush()
        return {"chapters_created": len(chapter_defs)}
