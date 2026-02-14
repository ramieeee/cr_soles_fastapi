from __future__ import annotations

from datetime import datetime

from sqlalchemy import Text, Integer, DateTime, func, text, ForeignKey, Identity
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.core.db import Base
from app.core.config import settings


class PapersStaging(Base):
    __tablename__ = "papers_staging"
    __table_args__ = {"schema": "soles"}

    idx: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("soles.papers.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    is_approved: Mapped[bool] = mapped_column(
        nullable=False, server_default=text("false")
    )
    approval_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        server_default=text("'{}'::text[]"),
    )
    journal: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer)
    abstract: Mapped[str | None] = mapped_column(Text)
    pdf_url: Mapped[str | None] = mapped_column(Text)
    ingestion_source: Mapped[str | None] = mapped_column(Text)
    ingestion_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.embedding_dimension)
    )

    paper = relationship(
        "Papers",
        back_populates="staging_items",
        primaryjoin="PapersStaging.id == Papers.id",
        foreign_keys=id,
        passive_deletes=True,
    )
