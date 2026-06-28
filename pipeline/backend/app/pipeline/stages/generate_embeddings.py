"""Stage 5: Generate sentence-transformer embeddings for each chapter."""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...models.db import Chapter
from ...services.embedder import embed_chapter
from .base import PipelineStage


class GenerateEmbeddingsStage(PipelineStage):
    name = "generate_embeddings"

    async def run(self, textbook_id: str, db: AsyncSession) -> dict:
        result = await db.execute(
            select(Chapter).where(Chapter.textbook_id == textbook_id)
        )
        chapters = result.scalars().all()
        embedded = 0

        for chapter in chapters:
            if chapter.embedding_status == "completed":
                embedded += 1
                continue  # resumable: skip already-embedded chapters

            # Run CPU-bound embedding in a thread pool
            loop = asyncio.get_event_loop()
            vector = await loop.run_in_executor(
                None,
                embed_chapter,
                chapter.title,
                chapter.extracted_json or {},
            )
            chapter.embedding = vector
            chapter.embedding_status = "completed"
            await db.flush()
            embedded += 1

        return {"chapters_embedded": embedded}
