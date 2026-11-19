from sqlalchemy import text


def test_engine_executes_select_one(db_engine):
    with db_engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar() == 1


def test_test_engine_enables_sqlite_foreign_keys(db_engine):
    with db_engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar() == 1


def test_metadata_contains_multiempresa_tables():
    from app.database.base import Base
    from app.models import Company, User

    assert "companies" in Base.metadata.tables
    assert "users" in Base.metadata.tables
    assert "company_id" in User.__table__.columns
    assert "company_id" not in Company.__table__.columns
