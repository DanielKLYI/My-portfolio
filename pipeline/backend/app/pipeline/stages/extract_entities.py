"""Stage 4: Extract clinical entities per chapter via Claude."""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...models.db import Chapter, Textbook
from ...services.extractor import extract_entities
from .base import PipelineStage

# Throttle concurrent Claude calls to avoid rate limits
_CONCURRENCY = 3


class ExtractEntitiesStage(PipelineStage):
    name = "extract_entities"

    async def run(self, textbook_id: str, db: AsyncSession) -> dict:
        result = await db.execute(
            select(Chapter).where(Chapter.textbook_id == textbook_id)
        )
        chapters = result.scalars().all()

        semaphore = asyncio.Semaphore(_CONCURRENCY)
        processed = 0

        async def _process(chapter: Chapter):
            nonlocal processed
            if chapter.extracted_json and chapter.extracted_json.get("diseases") is not None:
                processed += 1
                return  # already done, skip for resumability

            async with semaphore:
                entities = await extract_entities(chapter.title, chapter.content_markdown or "")
                chapter.extracted_json = entities
                await db.flush()

            processed += 1
            # Increment processed_chapters on the parent textbook
            book_result = await db.execute(select(Textbook).where(Textbook.id == textbook_id))
            book = book_result.scalar_one()
            book.processed_chapters = processed
            await db.flush()

        await asyncio.gather(*[_process(ch) for ch in chapters])
        await db.flush()
        return {"chapters_extracted": processed}
