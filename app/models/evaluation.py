from __future__ import annotations

from datetime import datetime

from sqlalchemy import Text, DateTime, func, text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.db import Base


class Evaluation(Base):
    __tablename__ = "evaluations"
    __table_args__ = {"schema": "soles"}

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    extraction_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("soles.extractions.id", ondelete="CASCADE"),
        nullable=False,
    )
    evaluator_id: Mapped[str] = mapped_column(Text, nullable=False)
    agreement_scores: Mapped[dict | None] = mapped_column(JSONB)
    notes: Mapped[str | None] = mapped_column(Text)
    evaluation_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    extraction = relationship(
        "Extraction",
        back_populates="evaluations",
        primaryjoin="Evaluation.extraction_id == Extraction.id",
        foreign_keys=extraction_id,
        passive_deletes=True,
    )
