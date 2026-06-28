"""Resumable pipeline runner — skips stages already completed in the DB."""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.db import Textbook
from .stages import STAGES
from .stages.base import get_stage_status

# textbook_id -> asyncio.Task, so the dashboard can check if it's running
_active: dict[str, asyncio.Task] = {}


async def run_pipeline(textbook_id: str, db: AsyncSession, force_restart: bool = False):
    """Run (or resume) all pipeline stages for a textbook."""
    for stage in STAGES:
        status = await get_stage_status(db, textbook_id, stage.name)

        if not force_restart and status == "completed":
            continue  # already done

        await stage.execute(textbook_id, db)

    # Mark textbook complete
    result = await db.execute(select(Textbook).where(Textbook.id == textbook_id))
    book = result.scalar_one()
    book.status = "completed"
    book.current_stage = None
    await db.commit()


def launch_pipeline(textbook_id: str, db: AsyncSession) -> asyncio.Task:
    """Launch the pipeline in a background asyncio task."""
    if textbook_id in _active and not _active[textbook_id].done():
        return _active[textbook_id]

    task = asyncio.create_task(_run_and_cleanup(textbook_id, db))
    _active[textbook_id] = task
    return task


async def _run_and_cleanup(textbook_id: str, db: AsyncSession):
    try:
        await run_pipeline(textbook_id, db)
    finally:
        _active.pop(textbook_id, None)


def is_running(textbook_id: str) -> bool:
    t = _active.get(textbook_id)
    return t is not None and not t.done()
