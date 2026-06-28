"""Upload endpoint — accepts a PDF and kicks off the pipeline."""
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles

from ..database import get_db
from ..models.db import Textbook
from ..pipeline.runner import launch_pipeline
from ..config import settings

router = APIRouter(prefix="/api/textbooks", tags=["upload"])


@router.post("/upload")
async def upload_textbook(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    textbook_id = str(uuid.uuid4())
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    dest = upload_dir / f"{textbook_id}.pdf"
    async with aiofiles.open(dest, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            await f.write(chunk)

    # Derive title from filename (strip extension)
    title = Path(file.filename).stem.replace("_", " ").replace("-", " ").title()

    book = Textbook(
        id=textbook_id,
        title=title,
        filename=file.filename,
        file_path=str(dest),
        status="uploaded",
    )
    db.add(book)
    await db.commit()

    launch_pipeline(textbook_id, db)

    return {"textbook_id": textbook_id, "title": title, "status": "processing"}
