import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.core.password import hash_password
from app.core.permissions import UserRole
from app.core.security import get_current_user
from app.database.base import Base
from app.database.session import create_database_engine, get_db
from app.main import app
from app.models import Company, User
from app.services.login_guard import login_guard

TEST_PASSWORD = "Senha@123"
TEST_PASSWORD_HASH = hash_password(TEST_PASSWORD)


@pytest.fixture(autouse=True)
def reset_login_guard():
    login_guard.clear_all()
    yield
    login_guard.clear_all()


@pytest.fixture
def db_engine():
    engine = create_database_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    session_factory = sessionmaker(
        bind=db_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    with session_factory() as session:
        yield session


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def companies(db_session):
    alpha = Company(
        legal_name="Oficina Alfa",
        trade_name="Alfa",
        document="12.345.678/0001-90",
    )
    beta = Company(
        legal_name="Assistência Beta",
        trade_name="Beta",
        document="98.765.432/0001-10",
    )
    db_session.add_all([alpha, beta])
    db_session.commit()
    return alpha, beta


@pytest.fixture
def users(db_session, companies):
    alpha, beta = companies
    ana = User(
        company_id=alpha.id,
        name="Ana Administradora",
        email="ana@alfa.example",
        password_hash=TEST_PASSWORD_HASH,
        role=UserRole.ADMIN,
    )
    carlos = User(
        company_id=beta.id,
        name="Carlos Técnico",
        email="carlos@beta.example",
        password_hash=TEST_PASSWORD_HASH,
        role=UserRole.TECHNICIAN,
    )
    db_session.add_all([ana, carlos])
    db_session.commit()
    return ana, carlos


@pytest.fixture
def team_users(db_session, companies):
    """Massa completa de usuários de `acceptance.md`, com senhas válidas."""

    alpha, beta = companies
    members = [
        User(company_id=alpha.id, name="Ana Administradora", email="ana@alfa.example",
             password_hash=TEST_PASSWORD_HASH, role=UserRole.ADMIN),
        User(company_id=alpha.id, name="Bruno Atendente", email="bruno@alfa.example",
             password_hash=TEST_PASSWORD_HASH, role=UserRole.ATTENDANT),
        User(company_id=alpha.id, name="Carlos Técnico", email="carlos@alfa.example",
             password_hash=TEST_PASSWORD_HASH, role=UserRole.TECHNICIAN),
        User(company_id=beta.id, name="Diana Administradora", email="diana@beta.example",
             password_hash=TEST_PASSWORD_HASH, role=UserRole.ADMIN),
        User(company_id=beta.id, name="Eduardo Técnico", email="eduardo@beta.example",
             password_hash=TEST_PASSWORD_HASH, role=UserRole.TECHNICIAN),
    ]
    db_session.add_all(members)
    db_session.commit()
    return {member.email.split("@")[0]: member for member in members}


@pytest.fixture
def login_as(client):
    def perform(email: str, password: str = TEST_PASSWORD):
        return client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )

    return perform


def auth_headers_from(client, response) -> dict[str, str]:
    assert response.status_code == 200, response.text
    csrf_token = client.cookies.get(get_settings().csrf_cookie_name)
    assert csrf_token, "Cookie CSRF não foi enviado no login."
    return {"X-CSRF-Token": csrf_token}


@pytest.fixture
def admin_auth(client, team_users, login_as):
    return auth_headers_from(client, login_as("ana@alfa.example"))


@pytest.fixture
def attendant_auth(client, team_users, login_as):
    return auth_headers_from(client, login_as("bruno@alfa.example"))


@pytest.fixture
def technician_auth(client, team_users, login_as):
    return auth_headers_from(client, login_as("carlos@alfa.example"))


@pytest.fixture
def beta_admin_auth(client, team_users, login_as):
    return auth_headers_from(client, login_as("diana@beta.example"))
