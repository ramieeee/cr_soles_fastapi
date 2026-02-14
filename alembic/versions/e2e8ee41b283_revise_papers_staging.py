"""Revise papers_staging

Revision ID: e2e8ee41b283
Revises: 20260214_0001
Create Date: 2026-02-14 22:16:21.566150

"""
from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "e2e8ee41b283"
down_revision = "20260214_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No-op: previous autogenerate included Supabase system schemas.
    # Keeping this revision empty avoids privilege errors on upgrade.
    pass


def downgrade() -> None:
    # No-op
    pass
