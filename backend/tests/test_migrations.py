import os
import sqlite3
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]

BASE_ENV = {
    **os.environ,
    "APP_ENV": "development",
    "APP_DEBUG": "true",
    "SECRET_KEY": "chave-ficticia-para-testes",
}


def run_alembic(*arguments: str, database_url: str | None = None):
    env = dict(BASE_ENV)
    if database_url is not None:
        env["DATABASE_URL"] = database_url
    return subprocess.run(
        [sys.executable, "-m", "alembic", *arguments],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_offline_migration_sql_contains_multiempresa_structure():
    result = run_alembic("upgrade", "head", "--sql")

    assert result.returncode == 0, result.stderr
    sql = result.stdout.lower()
    assert "create table companies" in sql
    assert "create table users" in sql
    assert "create table user_sessions" in sql
    assert "company_id" in sql
    assert "uq_users_email" in sql
    assert "csrf_token_hash" in sql


def test_offline_downgrade_removes_postgres_enum_type():
    result = run_alembic("downgrade", "head:base", "--sql")

    assert result.returncode == 0, result.stderr
    assert "drop type if exists user_role" in result.stdout.lower()


def test_migration_applies_and_reverts_on_database(tmp_path):
    database_url = f"sqlite:///{tmp_path.joinpath('migration.db').as_posix()}"

    upgrade = run_alembic("upgrade", "head", database_url=database_url)
    assert upgrade.returncode == 0, upgrade.stderr

    downgrade = run_alembic("downgrade", "base", database_url=database_url)
    assert downgrade.returncode == 0, downgrade.stderr

    with sqlite3.connect(tmp_path / "migration.db") as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert "companies" not in tables
    assert "users" not in tables
    assert "user_sessions" not in tables
