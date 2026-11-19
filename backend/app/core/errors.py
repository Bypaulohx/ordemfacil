import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("ordemfacil")


class AppError(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"
    message = "Não foi possível concluir a operação."

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        status_code: int | None = None,
        fields: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message or self.message)
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.fields = fields

    def payload(self) -> dict[str, Any]:
        detail: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.fields:
            detail["fields"] = self.fields
        return {"detail": detail}


class ValidationError(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"
    message = "Verifique os campos destacados."


class AuthenticationError(AppError):
    status_code = 401
    code = "UNAUTHORIZED"
    message = "Autenticação necessária."


class AuthorizationError(AppError):
    status_code = 403
    code = "FORBIDDEN"
    message = "Você não tem permissão para esta operação."


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"
    message = "Registro não encontrado."


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"
    message = "Conflito com registros existentes."


class BusinessRuleError(AppError):
    status_code = 400
    code = "BUSINESS_RULE_ERROR"
    message = "Operação não permitida."


class CSRFError(AppError):
    status_code = 403
    code = "CSRF_INVALID"
    message = "Token CSRF inválido ou ausente."


class RateLimitError(AppError):
    status_code = 429
    code = "TOO_MANY_ATTEMPTS"
    message = "Muitas tentativas de login. Tente novamente mais tarde."


HTTP_ERRORS: dict[int, tuple[str, str]] = {
    400: ("BAD_REQUEST", "Solicitação inválida."),
    401: ("UNAUTHORIZED", "Autenticação necessária."),
    403: ("FORBIDDEN", "Você não tem permissão para esta operação."),
    404: ("NOT_FOUND", "Recurso não encontrado."),
    405: ("METHOD_NOT_ALLOWED", "Método não permitido."),
    429: ("TOO_MANY_ATTEMPTS", "Muitas tentativas. Tente novamente mais tarde."),
}


def _error_response(
    status_code: int,
    code: str,
    message: str,
    fields: dict[str, Any] | None = None,
) -> JSONResponse:
    detail: dict[str, Any] = {"code": code, "message": message}
    if fields:
        detail["fields"] = fields
    return JSONResponse(status_code=status_code, content={"detail": detail})


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=exc.payload())


async def request_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    fields: dict[str, str] = {}
    for error in exc.errors():
        location = [
            str(part)
            for part in error.get("loc", ())
            if part not in {"body", "query", "path", "header", "cookie"}
        ]
        key = ".".join(location) if location else "corpo"
        fields.setdefault(key, str(error.get("msg", "Valor inválido.")))
    return _error_response(422, "VALIDATION_ERROR", "Verifique os campos destacados.", fields or None)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code, message = HTTP_ERRORS.get(
        exc.status_code,
        ("HTTP_ERROR", "Não foi possível concluir a operação."),
    )
    return _error_response(exc.status_code, code, message)


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Erro não tratado em %s %s", request.method, request.url.path)
    return _error_response(500, "INTERNAL_ERROR", "Erro interno do servidor.")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)
