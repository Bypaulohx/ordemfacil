from app.core.config import get_settings
from app.core.password import verify_password
from app.models import User

TEST_PASSWORD = "Senha@123"


def test_admin_lists_only_users_from_own_company(client, admin_auth, team_users, companies):
    response = client.get("/api/v1/users")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert {item["company_id"] for item in body["items"]} == {str(companies[0].id)}
    assert all("diana@beta.example" not in str(item) for item in body["items"])


def test_admin_creates_user_in_own_company_and_hashes_password(
    client, admin_auth, db_session, companies, team_users
):
    payload = {
        "name": "Novo Atendente",
        "email": "novo@alfa.example",
        "password": TEST_PASSWORD,
        "role": "ATTENDANT",
        "company_id": str(companies[1].id),  # tentativa de manipulação de escopo
    }

    response = client.post("/api/v1/users", json=payload, headers=admin_auth)

    assert response.status_code == 201
    body = response.json()
    assert body["company_id"] == str(companies[0].id)
    assert body["role"] == "ATTENDANT"
    assert "password_hash" not in body

    created = db_session.query(User).filter_by(email="novo@alfa.example").one()
    assert created.company_id == companies[0].id
    assert created.password_hash.startswith("$argon2id$")
    assert verify_password(TEST_PASSWORD, created.password_hash)


def test_duplicate_email_is_rejected_across_companies(client, admin_auth, team_users):
    response = client.post(
        "/api/v1/users",
        json={
            "name": "E-mail repetido",
            "email": "diana@beta.example",
            "password": TEST_PASSWORD,
            "role": "ATTENDANT",
        },
        headers=admin_auth,
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "CONFLICT"


def test_admin_can_consult_update_and_change_user_status(
    client, admin_auth, team_users, login_as
):
    bruno = team_users["bruno"]

    detail = client.get(f"/api/v1/users/{bruno.id}", headers=admin_auth)
    assert detail.status_code == 200
    assert detail.json()["name"] == "Bruno Atendente"

    updated = client.put(
        f"/api/v1/users/{bruno.id}",
        json={"name": "Bruno Atualizado", "role": "TECHNICIAN"},
        headers=admin_auth,
    )
    assert updated.status_code == 200
    assert updated.json()["role"] == "TECHNICIAN"

    inactive = client.patch(
        f"/api/v1/users/{bruno.id}/status",
        json={"is_active": False},
        headers=admin_auth,
    )
    assert inactive.status_code == 200
    assert inactive.json()["is_active"] is False
    assert login_as("bruno@alfa.example").status_code == 401


def test_update_replaces_password_hash(client, admin_auth, db_session, team_users):
    bruno = team_users["bruno"]
    old_hash = bruno.password_hash

    response = client.put(
        f"/api/v1/users/{bruno.id}",
        json={"password": "NovaSenha@456"},
        headers=admin_auth,
    )

    assert response.status_code == 200
    db_session.refresh(bruno)
    assert bruno.password_hash != old_hash
    assert verify_password("NovaSenha@456", bruno.password_hash)


def test_cross_company_user_access_is_hidden(client, beta_admin_auth, team_users):
    ana = team_users["ana"]

    assert client.get(f"/api/v1/users/{ana.id}").status_code == 404
    assert client.put(
        f"/api/v1/users/{ana.id}", json={"name": "Invasor"}, headers=beta_admin_auth
    ).status_code == 404
    assert client.patch(
        f"/api/v1/users/{ana.id}/status",
        json={"is_active": False},
        headers=beta_admin_auth,
    ).status_code == 404


def test_non_admins_cannot_manage_users(client, team_users, login_as):
    payload = {
        "name": "Negado",
        "email": "negado@alfa.example",
        "password": TEST_PASSWORD,
        "role": "ATTENDANT",
    }

    for email in ("bruno@alfa.example", "carlos@alfa.example"):
        assert login_as(email).status_code == 200
        headers = {
            "X-CSRF-Token": client.cookies.get(get_settings().csrf_cookie_name)
        }

        assert client.get("/api/v1/users").status_code == 403
        assert client.post("/api/v1/users", json=payload, headers=headers).status_code == 403
        assert client.patch(
            f"/api/v1/users/{team_users['ana'].id}/status",
            json={"is_active": False},
            headers=headers,
        ).status_code == 403


def test_user_creation_validation(client, admin_auth, team_users):
    invalid_payloads = [
        {"email": "sem-nome@alfa.example", "password": TEST_PASSWORD, "role": "ATTENDANT"},
        {"name": "E-mail inválido", "email": "invalido", "password": TEST_PASSWORD,
         "role": "ATTENDANT"},
        {"name": "Senha curta", "email": "curta@alfa.example", "password": "123",
         "role": "ATTENDANT"},
        {"name": "Perfil inválido", "email": "perfil@alfa.example", "password": TEST_PASSWORD,
         "role": "GERENTE"},
    ]

    for payload in invalid_payloads:
        response = client.post("/api/v1/users", json=payload, headers=admin_auth)
        assert response.status_code == 422, payload


def test_pagination_and_filters(client, admin_auth, team_users):
    second_page = client.get("/api/v1/users?page=2&page_size=2")
    assert second_page.status_code == 200
    assert second_page.json()["total"] == 3
    assert len(second_page.json()["items"]) == 1

    technicians = client.get("/api/v1/users?role=TECHNICIAN")
    assert [item["email"] for item in technicians.json()["items"]] == ["carlos@alfa.example"]

    search = client.get("/api/v1/users?search=diana")
    assert search.json()["total"] == 0  # usuária de outra empresa

    inactive = client.get("/api/v1/users?is_active=false")
    assert inactive.json()["total"] == 0
