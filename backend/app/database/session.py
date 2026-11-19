import sqlite3
from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()


def create_database_engine(
    database_url: str,
    *,
    echo: bool = False,
    connect_args: dict[str, Any] | None = None,
    poolclass: type | None = None,
) -> Engine:
    options: dict[str, Any] = {"pool_pre_ping": True, "echo": echo}
    if connect_args is not None:
        options["connect_args"] = connect_args
    if poolclass is not None:
        options["poolclass"] = poolclass

    engine = create_engine(database_url, **options)

    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def enable_sqlite_foreign_keys(
            dbapi_connection: Any, _connection_record: Any
        ) -> None:
            if isinstance(dbapi_connection, sqlite3.Connection):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    return engine


engine = create_database_engine(settings.database_url)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_database_connection(db: Session) -> None:
    db.execute(text("SELECT 1"))
