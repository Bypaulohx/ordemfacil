from app.core.config import get_settings


def test_cors_allows_configured_origin(client):
    origin = get_settings().cors_origins[0]

    response = client.get("/api/v1/health", headers={"Origin": origin})

    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_does_not_allow_unconfigured_origin(client):
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "https://origem-nao-autorizada.example"},
    )

    assert "access-control-allow-origin" not in response.headers
