"""Base stage interface and shared stage-run helpers."""
from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from ...models.db import PipelineStageRun, Textbook


class PipelineStage(ABC):
    name: str  # must be set on subclasses

    @abstractmethod
    async def run(self, textbook_id: str, db: AsyncSession) -> dict:
        """Execute the stage and return an output dict."""

    async def execute(self, textbook_id: str, db: AsyncSession) -> dict:
        """Wrapper: create/update stage run record, call run(), handle errors."""
        run = await _upsert_stage_run(db, textbook_id, self.name, "running")
        await _set_textbook_stage(db, textbook_id, self.name)
        try:
            output = await self.run(textbook_id, db)
            run.status = "completed"
            run.completed_at = datetime.now(timezone.utc)
            run.output = output
            await db.commit()
            return output
        except Exception as exc:
            run.status = "failed"
            run.completed_at = datetime.now(timezone.utc)
            run.error_message = str(exc)
            await db.commit()
            raise


async def get_stage_status(db: AsyncSession, textbook_id: str, stage: str) -> str | None:
    result = await db.execute(
        select(PipelineStageRun.status).where(
            PipelineStageRun.textbook_id == textbook_id,
            PipelineStageRun.stage == stage,
        )
    )
    return result.scalar_one_or_none()


async def _upsert_stage_run(db: AsyncSession, textbook_id: str, stage: str, status: str) -> PipelineStageRun:
    result = await db.execute(
        select(PipelineStageRun).where(
            PipelineStageRun.textbook_id == textbook_id,
            PipelineStageRun.stage == stage,
        )
    )
    run = result.scalar_one_or_none()
    if run is None:
        run = PipelineStageRun(
            textbook_id=textbook_id,
            stage=stage,
            status=status,
            started_at=datetime.now(timezone.utc),
        )
        db.add(run)
    else:
        run.status = status
        run.started_at = datetime.now(timezone.utc)
        run.error_message = None
    await db.flush()
    return run


async def _set_textbook_stage(db: AsyncSession, textbook_id: str, stage: str):
    result = await db.execute(select(Textbook).where(Textbook.id == textbook_id))
    book = result.scalar_one()
    book.current_stage = stage
    book.status = "processing"
    await db.flush()
