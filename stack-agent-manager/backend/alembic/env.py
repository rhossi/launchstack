from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection
import os

from alembic import context

from app.database import Base
from app.models import User, Stack, Agent

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get database URL from environment variable or alembic.ini
database_url = os.getenv("DATABASE_URL")
if not database_url:
    # Try to load from settings if .env file exists
    try:
        from app.config import settings
        database_url = settings.database_url
    except Exception:
        # Fallback to alembic.ini or use default
        database_url = config.get_main_option("sqlalchemy.url")
        if not database_url or database_url == "driver://user:pass@localhost/dbname":
            raise ValueError(
                "DATABASE_URL environment variable is required. "
                "Set it in your .env file or export it before running migrations."
            )

# Remove +asyncpg for Alembic (it uses sync SQLAlchemy with psycopg2)
if database_url and "+asyncpg" in database_url:
    database_url = database_url.replace("+asyncpg", "")

config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

