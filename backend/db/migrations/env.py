"""Alembic environment configuration."""

import sys
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add backend/ to path so imports work
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config import DATABASE_URL
from db.models import Base

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(url=DATABASE_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    from sqlalchemy import create_engine
    connectable = create_engine(DATABASE_URL)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
