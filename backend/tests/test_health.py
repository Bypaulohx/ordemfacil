def test_api_health_returns_ok(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app"] == "OrdemFacil"
    assert body["environment"] == "development"


def test_root_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_route_uses_standard_error_format(client):
    response = client.get("/rota-inexistente")

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "code": "NOT_FOUND",
            "message": "Recurso não encontrado.",
        }
    }
