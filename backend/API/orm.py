"""SQLAlchemy reflection and session helpers for the existing MySQL schema."""

from contextlib import contextmanager

from flask import current_app
from sqlalchemy import URL, create_engine, select
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker


def configure_orm(app):
    engine_url = URL.create(
        "mysql+mysqldb",
        username=app.config["MYSQL_USER"],
        password=app.config["MYSQL_PASSWORD"],
        host=app.config["MYSQL_HOST"],
        port=app.config["MYSQL_PORT"],
        database=app.config["MYSQL_DB"],
        query={"charset": "utf8mb4"},
    )
    engine = create_engine(engine_url, pool_pre_ping=True, pool_recycle=1800)
    base = automap_base()
    base.prepare(autoload_with=engine)

    app.extensions["marqueza.orm.engine"] = engine
    app.extensions["marqueza.orm.base"] = base
    app.extensions["marqueza.orm.sessions"] = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )


def orm_model(table_name):
    base = current_app.extensions["marqueza.orm.base"]
    try:
        return getattr(base.classes, table_name.lower())
    except AttributeError as error:
        raise LookupError(f"No hay un modelo ORM para la tabla {table_name!r}.") from error


def orm_list(table_name, output_type):
    model = orm_model(table_name)
    primary_key = model.__mapper__.primary_key[0]
    with orm_session() as session:
        rows = session.scalars(select(model).order_by(primary_key)).all()
        return [
            output_type(*(getattr(row, column.key) for column in model.__table__.columns)).to_dic()
            for row in rows
        ]


def orm_insert(table_name, values):
    model = orm_model(table_name)
    with orm_session() as session:
        session.add(model(**values))


def orm_update(table_name, record_id, values):
    model = orm_model(table_name)
    with orm_session() as session:
        row = session.get(model, int(record_id))
        if row is not None:
            for column, value in values.items():
                setattr(row, column, value)


def orm_delete(table_name, record_id):
    model = orm_model(table_name)
    with orm_session() as session:
        row = session.get(model, int(record_id))
        if row is not None:
            session.delete(row)


@contextmanager
def orm_session():
    session_factory = current_app.extensions["marqueza.orm.sessions"]
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()