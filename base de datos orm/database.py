"""SQLAlchemy reflection helpers for the existing MySQL schema."""

import os

from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker


def load_database(database_url=None):
    url = database_url or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("Define DATABASE_URL antes de conectar con la base de datos.")

    engine = create_engine(url, pool_pre_ping=True)
    base = automap_base()
    base.prepare(autoload_with=engine)
    session_local = sessionmaker(bind=engine, expire_on_commit=False)
    return engine, base, session_local


def model_for_table(base, table_name):
    for mapper in base.registry.mappers:
        if mapper.local_table.name == table_name:
            return mapper.class_
    raise LookupError(f"No existe una tabla reflejada llamada {table_name!r}.")
