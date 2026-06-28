"""Semantic search endpoint using pgvector cosine similarity."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..database import get_db
from ..services.embedder import embed_query

router = APIRouter(prefix="/api", tags=["search"])


class SearchRequest(BaseModel):
    query: str
    textbook_id: str | None = None
    limit: int = 10


@router.post("/search")
async def semantic_search(req: SearchRequest, db: AsyncSession = Depends(get_db)):
    vector = embed_query(req.query)
    vec_str = "[" + ",".join(str(v) for v in vector) + "]"

    base_sql = """
        SELECT
            c.id,
            c.textbook_id,
            c.chapter_number,
            c.title,
            c.page_start,
            c.page_end,
            c.extracted_json,
            t.title AS textbook_title,
            1 - (c.embedding <=> :vec::vector) AS score
        FROM chapters c
        JOIN textbooks t ON t.id = c.textbook_id
        WHERE c.embedding IS NOT NULL
        {where_clause}
        ORDER BY c.embedding <=> :vec::vector
        LIMIT :limit
    """

    where_clause = "AND c.textbook_id = :textbook_id" if req.textbook_id else ""
    sql = text(base_sql.format(where_clause=where_clause))

    params: dict = {"vec": vec_str, "limit": req.limit}
    if req.textbook_id:
        params["textbook_id"] = req.textbook_id

    result = await db.execute(sql, params)
    rows = result.mappings().all()

    return [
        {
            "chapter_id": str(row["id"]),
            "textbook_id": str(row["textbook_id"]),
            "textbook_title": row["textbook_title"],
            "chapter_number": row["chapter_number"],
            "title": row["title"],
            "page_start": row["page_start"],
            "page_end": row["page_end"],
            "score": round(float(row["score"]), 4),
            "extracted_json": row["extracted_json"],
        }
        for row in rows
    ]
