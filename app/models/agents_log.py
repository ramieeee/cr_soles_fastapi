from __future__ import annotations

from datetime import datetime

from sqlalchemy import Text, DateTime, func, text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.db import Base


class AgentLog(Base):
    __tablename__ = "agents_logs"
    __table_args__ = {"schema": "soles"}

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    paper_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("soles.papers.id", ondelete="SET NULL"),
    )
    extraction_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("soles.extractions.id", ondelete="SET NULL"),
    )
    agent_name: Mapped[str] = mapped_column(Text, nullable=False)
    raw_output: Mapped[str | None] = mapped_column(Text)
    cleaned_output: Mapped[dict | None] = mapped_column(JSONB)
    input: Mapped[str | None] = mapped_column(Text)
    node_name: Mapped[str | None] = mapped_column(Text)
    prompt_hash: Mapped[str | None] = mapped_column(Text)
    model_name: Mapped[str | None] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    paper = relationship(
        "Paper",
        back_populates="agents_logs",
        primaryjoin="AgentLog.paper_id == Paper.id",
        foreign_keys=paper_id,
        passive_deletes=True,
    )
    extraction = relationship(
        "Extraction",
        back_populates="agents_logs",
        primaryjoin="AgentLog.extraction_id == Extraction.id",
        foreign_keys=extraction_id,
        passive_deletes=True,
    )
