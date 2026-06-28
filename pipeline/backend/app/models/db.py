import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from ..database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Textbook(Base):
    __tablename__ = "textbooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    filename = Column(Text, nullable=False)
    file_path = Column(Text, nullable=False)
    status = Column(String(50), default="uploaded", nullable=False)
    current_stage = Column(String(100))
    total_chapters = Column(Integer, default=0)
    processed_chapters = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    metadata_ = Column("metadata", JSON, default=dict)


class PipelineStageRun(Base):
    __tablename__ = "pipeline_stage_runs"
    __table_args__ = (UniqueConstraint("textbook_id", "stage"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    textbook_id = Column(UUID(as_uuid=True), ForeignKey("textbooks.id", ondelete="CASCADE"), nullable=False)
    stage = Column(String(100), nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    output = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class Chapter(Base):
    __tablename__ = "chapters"
    __table_args__ = (UniqueConstraint("textbook_id", "chapter_number"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    textbook_id = Column(UUID(as_uuid=True), ForeignKey("textbooks.id", ondelete="CASCADE"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    title = Column(Text, nullable=False)
    content_markdown = Column(Text)
    page_start = Column(Integer)
    page_end = Column(Integer)
    extracted_json = Column(JSON, default=dict)
    embedding = Column(Vector(384))
    embedding_status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
