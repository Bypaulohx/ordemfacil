from app.core.config import get_settings

TEST_PASSWORD = "Senha@123"
NEW_USER = {
    "name": "Novo Usuário",
    "email": "novo@alfa.example",
    "password": TEST_PASSWORD,
    "role": "ATTENDANT",
}


def test_write_without_csrf_token_is_rejected(client, team_users, login_as):
    response = login_as("ana@alfa.example")
    assert response.status_code == 200

    create = client.post("/api/v1/users", json=NEW_USER)

    assert create.status_code == 403
    assert create.json()["detail"]["code"] == "CSRF_INVALID"
    assert client.get("/api/v1/auth/me").status_code == 200


def test_csrf_header_must_match_cookie(client, team_users, login_as):
    login_as("ana@alfa.example")
    csrf_token = client.cookies.get(get_settings().csrf_cookie_name)

    mismatch = client.post(
        "/api/v1/users",
        json=NEW_USER,
        headers={"X-CSRF-Token": "token-diferente"},
    )
    assert mismatch.status_code == 403

    valid = client.post(
        "/api/v1/users",
        json=NEW_USER,
        headers={"X-CSRF-Token": csrf_token},
    )
    assert valid.status_code == 201


def test_forged_csrf_token_is_rejected_even_if_cookie_and_header_match(
    client, team_users, login_as
):
    login_as("ana@alfa.example")
    settings = get_settings()
    session_token = client.cookies.get(settings.session_cookie_name)

    client.cookies.clear()
    client.cookies.set(settings.session_cookie_name, session_token)
    client.cookies.set(settings.csrf_cookie_name, "token-forjado")

    response = client.post(
        "/api/v1/users",
        json=NEW_USER,
        headers={"X-CSRF-Token": "token-forjado"},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "CSRF_INVALID"


def test_logout_requires_csrf(client, team_users, login_as):
    login_as("ana@alfa.example")

    response = client.post("/api/v1/auth/logout")

    assert response.status_code == 403
    assert client.get("/api/v1/auth/me").status_code == 200
