"""
Alembic environment configuration for Ingress leaderboard bot.

This module configures the Alembic migration environment, sets up the database
connection, and imports all models to ensure they are available for migrations.
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import all models to ensure they're registered with SQLAlchemy
from src.database.models import Base  # noqa: F401,E402
from src.database.connection import get_database_connection  # noqa: F402,E402

# Get the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the SQLAlchemy URL from our configuration
db = get_database_connection()
config.set_main_option("sqlalchemy.url", db.database_url)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            # Include user-defined compare functions
            render_item=render_item,
        )

        with context.begin_transaction():
            context.run_migrations()


def render_item(type_, obj, autogen_context):
    """Custom rendering for migration items."""
    # Handle enum types with PostgreSQL
    if type_ == "type" and obj.name == "VARCHAR":
        # Customize VARCHAR rendering
        return "VARCHAR%(length)s" if obj.length else "VARCHAR"
    return False  # Use default rendering


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()