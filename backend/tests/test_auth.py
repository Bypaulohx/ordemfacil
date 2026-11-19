from datetime import timedelta

from app.core.config import get_settings
from app.core.password import verify_password
from app.models import User, UserSession
from app.services.sessions import hash_token, utc_now

TEST_PASSWORD = "Senha@123"


def _cookie(response, name: str) -> str | None:
    for value in response.headers.get_list("set-cookie"):
        if value.startswith(f"{name}="):
            return value
    return None


def test_login_creates_session_with_secure_cookies(client, team_users, login_as, db_session):
    response = login_as("ana@alfa.example")
    settings = get_settings()

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "ana@alfa.example"
    assert body["role"] == "ADMIN"
    assert "password_hash" not in body
    assert "password" not in body

    session_cookie = _cookie(response, settings.session_cookie_name)
    csrf_cookie = _cookie(response, settings.csrf_cookie_name)
    assert session_cookie is not None
    assert "HttpOnly" in session_cookie
    assert "SameSite=lax" in session_cookie
    assert csrf_cookie is not None
    assert "HttpOnly" not in csrf_cookie

    raw_token = client.cookies.get(settings.session_cookie_name)
    raw_csrf = client.cookies.get(settings.csrf_cookie_name)
    session = db_session.query(UserSession).one()
    assert session.token_hash == hash_token(raw_token)
    assert session.csrf_token_hash == hash_token(raw_csrf)
    assert session.revoked_at is None


def test_login_failure_messages_are_generic(client, users, login_as):
    wrong_password = login_as("ana@alfa.example", password="senha-errada")
    unknown_email = login_as("inexistente@example.com", password=TEST_PASSWORD)

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()
    message = unknown_email.json()["detail"]["message"]
    assert "inexistente@example.com" not in message
    assert "ana@alfa.example" not in message
    assert get_settings().session_cookie_name not in [
        cookie.split("=")[0] for cookie in unknown_email.headers.get_list("set-cookie")
    ]


def test_inactive_user_cannot_login(client, db_session, users, login_as):
    ana, _ = users
    ana.is_active = False
    db_session.commit()

    response = login_as("ana@alfa.example")

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "UNAUTHORIZED"


def test_inactive_company_blocks_login(client, db_session, companies, users, login_as):
    alpha, _ = companies
    alpha.is_active = False
    db_session.commit()

    response = login_as("ana@alfa.example")

    assert response.status_code == 401


def test_protected_endpoint_without_session_returns_401(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "UNAUTHORIZED"


def test_me_returns_user_and_company_without_secrets(client, admin_auth, team_users, companies):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Ana Administradora"
    assert body["role"] == "ADMIN"
    assert body["company"]["legal_name"] == "Oficina Alfa"
    assert body["company"]["id"] == str(companies[0].id)
    assert "password_hash" not in body
    assert "csrf_token_hash" not in body
    assert "token" not in body


def test_logout_revokes_session_and_removes_cookies(client, admin_auth, db_session):
    token = client.cookies.get(get_settings().session_cookie_name)

    response = client.post("/api/v1/auth/logout", headers=admin_auth)
    settings = get_settings()

    assert response.status_code == 204
    assert response.text == ""
    session = db_session.query(UserSession).filter_by(
        token_hash=hash_token(token)
    ).one()
    assert session.revoked_at is not None
    for name in (settings.session_cookie_name, settings.csrf_cookie_name):
        cookie = _cookie(response, name)
        assert cookie is not None
        assert "Max-Age=0" in cookie
    assert client.get("/api/v1/auth/me").status_code == 401


def test_expired_session_is_rejected(client, admin_auth, db_session):
    token = client.cookies.get(get_settings().session_cookie_name)
    session = db_session.query(UserSession).filter_by(token_hash=hash_token(token)).one()
    session.expires_at = utc_now() - timedelta(minutes=1)
    db_session.commit()

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_login_rate_limit_blocks_excessive_attempts(client, users, login_as):
    settings = get_settings()

    for _ in range(settings.login_max_attempts):
        assert login_as("ana@alfa.example", password="errada").status_code == 401

    blocked = login_as("ana@alfa.example", password=TEST_PASSWORD)
    assert blocked.status_code == 429
    assert blocked.json()["detail"]["code"] == "TOO_MANY_ATTEMPTS"


def test_successful_login_resets_failed_attempts(client, users, login_as):
    settings = get_settings()

    for _ in range(settings.login_max_attempts - 1):
        login_as("ana@alfa.example", password="errada")

    assert login_as("ana@alfa.example").status_code == 200
    assert login_as("ana@alfa.example", password="errada").status_code == 401


def test_password_from_database_is_a_verifiable_hash(client, admin_auth, db_session, team_users):
    ana = db_session.get(User, team_users["ana"].id)

    assert ana.password_hash.startswith("$argon2id$")
    assert verify_password(TEST_PASSWORD, ana.password_hash)
