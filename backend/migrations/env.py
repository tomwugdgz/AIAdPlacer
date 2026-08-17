"""Alembic 异步环境（async env）。

- 使用 asyncpg 异步引擎；
- target_metadata 取 app.models.Base.metadata（Booking 模型已挂同一 Base）；
- 在 run_sync 中执行迁移，兼容原生 DDL（btree_gist / 枚举 / EXCLUDE 约束）。
"""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.config import settings

# 导入模型以填充 metadata（含 Booking / LockTierConfig / MediaLevelRule）
from app.models import Base  # noqa: F401

config = context.config

# 动态覆盖为异步 URL（避免 ini 中明文重复）
config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1),
)

if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except Exception:  # noqa: BLE001
        pass

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
