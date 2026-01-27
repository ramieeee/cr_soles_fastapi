"""Initial schema

Revision ID: 20260127_0001
Revises: None
Create Date: 2026-01-27 00:00:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260127_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE SCHEMA IF NOT EXISTS soles")

    op.create_table(
        "papers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column(
            "authors",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::text[]"),
        ),
        sa.Column("journal", sa.Text()),
        sa.Column("year", sa.Integer()),
        sa.Column("abstract", sa.Text()),
        sa.Column("pdf_url", sa.Text()),
        sa.Column("ingestion_source", sa.Text()),
        sa.Column(
            "ingestion_timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("embedding", Vector(1024)),
        schema="soles",
    )

    op.create_table(
        "extractions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "paper_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("soles.papers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("extraction_version", sa.Text(), nullable=False),
        sa.Column("metadata_jsonb", postgresql.JSONB()),
        sa.Column("study_design_jsonb", postgresql.JSONB()),
        sa.Column("sample_jsonb", postgresql.JSONB()),
        sa.Column("outcomes_jsonb", postgresql.JSONB()),
        sa.Column("risk_of_bias_jsonb", postgresql.JSONB()),
        sa.Column(
            "extraction_timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("status", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "status IN ('success', 'partial', 'failed')",
            name="ck_extractions_status",
        ),
        schema="soles",
    )

    op.create_index(
        "idx_extractions_paper_id",
        "extractions",
        ["paper_id"],
        schema="soles",
    )
    op.create_index(
        "idx_extractions_paper_time",
        "extractions",
        ["paper_id", "extraction_timestamp"],
        schema="soles",
    )
    op.create_index(
        "idx_extractions_status",
        "extractions",
        ["status"],
        schema="soles",
    )

    op.create_table(
        "evaluations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "extraction_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("soles.extractions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("evaluator_id", sa.Text(), nullable=False),
        sa.Column("agreement_scores", postgresql.JSONB()),
        sa.Column("notes", sa.Text()),
        sa.Column(
            "evaluation_timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        schema="soles",
    )

    op.create_index(
        "idx_evaluations_extraction_id",
        "evaluations",
        ["extraction_id"],
        schema="soles",
    )
    op.create_index(
        "idx_evaluations_evaluator_id",
        "evaluations",
        ["evaluator_id"],
        schema="soles",
    )
    op.create_index(
        "idx_evaluations_time",
        "evaluations",
        ["evaluation_timestamp"],
        schema="soles",
    )

    op.create_table(
        "agents_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "paper_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("soles.papers.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "extraction_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("soles.extractions.id", ondelete="SET NULL"),
        ),
        sa.Column("agent_name", sa.Text(), nullable=False),
        sa.Column("raw_output", sa.Text()),
        sa.Column("cleaned_output", postgresql.JSONB()),
        sa.Column("input", sa.Text()),
        sa.Column("node_name", sa.Text()),
        sa.Column("prompt_hash", sa.Text()),
        sa.Column("model_name", sa.Text()),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        schema="soles",
    )

    op.create_index(
        "idx_agents_logs_paper_id",
        "agents_logs",
        ["paper_id"],
        schema="soles",
    )
    op.create_index(
        "idx_agents_logs_extraction_id",
        "agents_logs",
        ["extraction_id"],
        schema="soles",
    )
    op.create_index(
        "idx_agents_logs_agent_name",
        "agents_logs",
        ["agent_name"],
        schema="soles",
    )
    op.create_index(
        "idx_agents_logs_node_name",
        "agents_logs",
        ["node_name"],
        schema="soles",
    )
    op.create_index(
        "idx_agents_logs_time",
        "agents_logs",
        ["timestamp"],
        schema="soles",
    )
    op.create_index(
        "idx_agents_logs_prompt_hash",
        "agents_logs",
        ["prompt_hash"],
        schema="soles",
    )


def downgrade() -> None:
    op.drop_index("idx_agents_logs_prompt_hash", table_name="agents_logs", schema="soles")
    op.drop_index("idx_agents_logs_time", table_name="agents_logs", schema="soles")
    op.drop_index("idx_agents_logs_node_name", table_name="agents_logs", schema="soles")
    op.drop_index("idx_agents_logs_agent_name", table_name="agents_logs", schema="soles")
    op.drop_index("idx_agents_logs_extraction_id", table_name="agents_logs", schema="soles")
    op.drop_index("idx_agents_logs_paper_id", table_name="agents_logs", schema="soles")
    op.drop_table("agents_logs", schema="soles")

    op.drop_index("idx_evaluations_time", table_name="evaluations", schema="soles")
    op.drop_index("idx_evaluations_evaluator_id", table_name="evaluations", schema="soles")
    op.drop_index("idx_evaluations_extraction_id", table_name="evaluations", schema="soles")
    op.drop_table("evaluations", schema="soles")

    op.drop_index("idx_extractions_status", table_name="extractions", schema="soles")
    op.drop_index("idx_extractions_paper_time", table_name="extractions", schema="soles")
    op.drop_index("idx_extractions_paper_id", table_name="extractions", schema="soles")
    op.drop_table("extractions", schema="soles")

    op.drop_table("papers", schema="soles")
    op.execute("DROP SCHEMA IF EXISTS soles")
