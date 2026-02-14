from __future__ import annotations

import os
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.config import settings
from app.models import Base  # noqa: E402

# import app.models  # noqa: E402,F401

config = context.config

config.set_main_option("sqlalchemy.url", settings.supabase_db_url)

target_metadata = Base.metadata

ALLOWED_SCHEMAS = {"public", "soles"}  # <-- 본인 스키마에 맞게 조정


def include_name(name, type_, parent_names):
    schema = parent_names.get("schema_name")
    # schema가 None인 경우는 기본 스키마로 취급될 수 있어 public로 간주
    schema = schema or "public"
    return schema in ALLOWED_SCHEMAS


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_name=include_name,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
