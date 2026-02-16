from __future__ import annotations

from datetime import datetime

from sqlalchemy import Text, DateTime, func, CheckConstraint, text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.db import Base


class Extractions(Base):
    __tablename__ = "extractions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('success', 'partial', 'failed')",
            name="ck_extractions_status",
        ),
        {"schema": "cr_soles"},
    )

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    paper_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cr_soles.papers.id", ondelete="CASCADE"),
        nullable=False,
    )
    extraction_version: Mapped[str] = mapped_column(Text, nullable=False)

    metadata_jsonb: Mapped[dict | None] = mapped_column(JSONB)
    study_design_jsonb: Mapped[dict | None] = mapped_column(JSONB)
    sample_jsonb: Mapped[dict | None] = mapped_column(JSONB)
    outcomes_jsonb: Mapped[dict | None] = mapped_column(JSONB)
    risk_of_bias_jsonb: Mapped[dict | None] = mapped_column(JSONB)

    extraction_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)

    papers = relationship(
        "Papers",
        back_populates="extractions",
        primaryjoin="Extractions.paper_id == Papers.id",
        foreign_keys=paper_id,
        passive_deletes=True,
    )
    evaluations = relationship(
        "Evaluations",
        back_populates="extractions",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    agents_logs = relationship(
        "AgentLogs",
        back_populates="extractions",
        passive_deletes=True,
    )
