from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.errors import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    register_exception_handlers,
)


class Payload(BaseModel):
    valor: int


def build_client(*, raise_server_exceptions: bool = True) -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.post("/validacao")
    def validacao(payload: Payload):
        return payload.model_dump()

    @app.get("/autenticacao")
    def autenticacao():
        raise AuthenticationError()

    @app.get("/autorizacao")
    def autorizacao():
        raise AuthorizationError()

    @app.get("/nao-encontrado")
    def nao_encontrado():
        raise NotFoundError("OS não encontrada.")

    @app.get("/conflito")
    def conflito():
        raise ConflictError()

    @app.get("/regra")
    def regra():
        raise BusinessRuleError("Transição inválida.")

    @app.get("/inesperado")
    def inesperado():
        raise RuntimeError("segredo-que-nao-deve-vazar")

    return TestClient(app, raise_server_exceptions=raise_server_exceptions)


def test_validation_error_returns_fields():
    response = build_client().post("/validacao", json={"valor": "texto"})

    assert response.status_code == 422
    body = response.json()["detail"]
    assert body["code"] == "VALIDATION_ERROR"
    assert "valor" in body["fields"]


def test_authentication_and_authorization_errors():
    client = build_client()

    unauthorized = client.get("/autenticacao")
    forbidden = client.get("/autorizacao")

    assert unauthorized.status_code == 401
    assert unauthorized.json()["detail"]["code"] == "UNAUTHORIZED"
    assert forbidden.status_code == 403
    assert forbidden.json()["detail"]["code"] == "FORBIDDEN"


def test_not_found_conflict_and_business_rule_errors():
    client = build_client()

    not_found = client.get("/nao-encontrado")
    conflict = client.get("/conflito")
    rule = client.get("/regra")

    assert not_found.status_code == 404
    assert not_found.json()["detail"]["message"] == "OS não encontrada."
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["code"] == "CONFLICT"
    assert rule.status_code == 400
    assert rule.json()["detail"]["code"] == "BUSINESS_RULE_ERROR"


def test_unexpected_error_does_not_expose_details():
    response = build_client(raise_server_exceptions=False).get("/inesperado")

    assert response.status_code == 500
    assert response.json() == {
        "detail": {
            "code": "INTERNAL_ERROR",
            "message": "Erro interno do servidor.",
        }
    }
    assert "segredo-que-nao-deve-vazar" not in response.text
