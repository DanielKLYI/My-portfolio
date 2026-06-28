"""Admin endpoints — textbook list, pipeline status, chapter browser, SSE progress."""
import asyncio
import json
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models.db import Textbook, PipelineStageRun, Chapter
from ..pipeline.runner import launch_pipeline, is_running
from ..pipeline.stages import STAGES

router = APIRouter(prefix="/api", tags=["admin"])


# ── Textbooks ─────────────────────────────────────────────────────────────────

@router.get("/textbooks")
async def list_textbooks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Textbook).order_by(Textbook.created_at.desc()))
    books = result.scalars().all()
    return [_book_dict(b) for b in books]


@router.get("/textbooks/{textbook_id}")
async def get_textbook(textbook_id: str, db: AsyncSession = Depends(get_db)):
    book = await _get_book_or_404(textbook_id, db)
    stages = await _stage_statuses(textbook_id, db)
    return {**_book_dict(book), "stages": stages}


@router.post("/textbooks/{textbook_id}/resume")
async def resume_pipeline(textbook_id: str, db: AsyncSession = Depends(get_db)):
    await _get_book_or_404(textbook_id, db)
    if is_running(textbook_id):
        return {"message": "pipeline already running"}
    launch_pipeline(textbook_id, db)
    return {"message": "pipeline resumed"}


# ── Chapters ──────────────────────────────────────────────────────────────────

@router.get("/textbooks/{textbook_id}/chapters")
async def list_chapters(textbook_id: str, db: AsyncSession = Depends(get_db)):
    await _get_book_or_404(textbook_id, db)
    result = await db.execute(
        select(Chapter)
        .where(Chapter.textbook_id == textbook_id)
        .order_by(Chapter.chapter_number)
    )
    chapters = result.scalars().all()
    return [_chapter_summary(ch) for ch in chapters]


@router.get("/chapters/{chapter_id}")
async def get_chapter(chapter_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Chapter).where(Chapter.id == chapter_id))
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return _chapter_full(chapter)


# ── SSE progress stream ────────────────────────────────────────────────────────

@router.get("/events/{textbook_id}")
async def sse_progress(textbook_id: str, db: AsyncSession = Depends(get_db)):
    await _get_book_or_404(textbook_id, db)

    async def event_generator() -> AsyncGenerator[str, None]:
        while True:
            result = await db.execute(select(Textbook).where(Textbook.id == textbook_id))
            book = result.scalar_one()
            stages = await _stage_statuses(textbook_id, db)
            payload = json.dumps({**_book_dict(book), "stages": stages})
            yield f"data: {payload}\n\n"

            if book.status in ("completed", "failed"):
                break
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_book_or_404(textbook_id: str, db: AsyncSession) -> Textbook:
    result = await db.execute(select(Textbook).where(Textbook.id == textbook_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Textbook not found")
    return book


async def _stage_statuses(textbook_id: str, db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(PipelineStageRun).where(PipelineStageRun.textbook_id == textbook_id)
    )
    runs = {r.stage: r for r in result.scalars().all()}
    return [
        {
            "name": stage.name,
            "status": runs[stage.name].status if stage.name in runs else "pending",
            "error": runs[stage.name].error_message if stage.name in runs else None,
        }
        for stage in STAGES
    ]


def _book_dict(book: Textbook) -> dict:
    return {
        "id": str(book.id),
        "title": book.title,
        "filename": book.filename,
        "status": book.status,
        "current_stage": book.current_stage,
        "total_chapters": book.total_chapters,
        "processed_chapters": book.processed_chapters,
        "created_at": book.created_at.isoformat() if book.created_at else None,
    }


def _chapter_summary(ch: Chapter) -> dict:
    return {
        "id": str(ch.id),
        "chapter_number": ch.chapter_number,
        "title": ch.title,
        "page_start": ch.page_start,
        "page_end": ch.page_end,
        "embedding_status": ch.embedding_status,
        "has_extraction": bool(ch.extracted_json and ch.extracted_json.get("diseases") is not None),
    }


def _chapter_full(ch: Chapter) -> dict:
    return {
        **_chapter_summary(ch),
        "content_markdown": ch.content_markdown,
        "extracted_json": ch.extracted_json,
    }
