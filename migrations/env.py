from logging.config import fileConfig

import os

from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context

import sys
from os.path import dirname, abspath

ROOT_DIR = dirname(dirname(abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from dotenv import load_dotenv

# Running alembic from the host: read the repo-root .env. Inside Docker the
# variables are already set by docker-compose and are not overridden.
load_dotenv(os.path.join(ROOT_DIR, ".env"))

from app.database.database import db

# Import every model so autogenerate sees all tables.
from app.models.user import User  # noqa: F401
from app.models.accommodation import Accommodation  # noqa: F401

config = context.config


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = db.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_engine(get_database_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
