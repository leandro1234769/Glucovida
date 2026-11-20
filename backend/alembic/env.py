import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from app.database.base import Base

# Importar el paquete registra todos los modelos en metadata.
import app.models  # noqa: F401


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Obtener la URL desde el entorno.
# Alembic utiliza conexión síncrona para las migraciones.
database_url = os.getenv("DATABASE_URL")

if database_url:
    config.set_main_option(
        "sqlalchemy.url",
        database_url.replace("%", "%%"),
    )


target_metadata = Base.metadata


def include_name(name, type_, parent_names):
    """
    Limitar la inspección de Alembic al esquema glucovida.

    Evita que autogenerate intente gestionar accidentalmente
    tablas pertenecientes a otros esquemas de PostgreSQL.
    """

    if type_ == "schema":
        return name == "glucovida"

    if type_ == "table":
        return parent_names.get("schema_name") == "glucovida"

    return True


def run_migrations_offline() -> None:

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_name=include_name,
        compare_type=True,
        compare_server_default=True,
        version_table_schema="glucovida",
    )

    with context.begin_transaction():
        context.execute("CREATE SCHEMA IF NOT EXISTS glucovida")
        context.run_migrations()


def run_migrations_online() -> None:

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {},
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_name=include_name,
            compare_type=True,
            compare_server_default=True,
            version_table_schema="glucovida",
        )

        with context.begin_transaction():
            context.execute("CREATE SCHEMA IF NOT EXISTS glucovida")
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()