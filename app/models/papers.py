from __future__ import annotations

from datetime import datetime

from sqlalchemy import Text, Integer, DateTime, func, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.core.db import Base
from app.core.config import settings


class Papers(Base):
    __tablename__ = "papers"
    __table_args__ = {"schema": "soles"}

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
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

    extractions = relationship(
        "Extractions",
        back_populates="papers",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    agents_logs = relationship(
        "AgentLogs",
        back_populates="papers",
        passive_deletes=True,
    )
