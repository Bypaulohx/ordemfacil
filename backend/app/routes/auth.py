"""Endpoints de autenticação por sessão server-side."""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import AuthenticationError, NotFoundError, RateLimitError
from app.core.security import CurrentUser, get_current_user
from app.core.tenant import TenantScope, get_tenant_scope
from app.database.session import get_db
from app.models import Company, User
from app.schemas.auth import CompanySummary, CurrentUserResponse, LoginRequest
from app.schemas.user import UserResponse
from app.services.auth import authenticate_user
from app.services.login_guard import login_guard
from app.services.sessions import (
    IssuedSession,
    create_session,
    get_active_session,
    revoke_session,
)

router = APIRouter(prefix="/auth", tags=["autenticação"])


def set_session_cookies(
    response: Response,
    issued: IssuedSession,
    settings: Settings,
) -> None:
    max_age = settings.session_expire_minutes * 60
    common = {
        "max_age": max_age,
        "path": "/",
        "secure": settings.session_cookie_secure,
        "samesite": settings.session_cookie_samesite,
    }
    response.set_cookie(
        key=settings.session_cookie_name,
        value=issued.token,
        httponly=True,
        **common,
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=issued.csrf_token,
        httponly=False,
        **common,
    )


def delete_session_cookies(response: Response, settings: Settings) -> None:
    for cookie_name in (settings.session_cookie_name, settings.csrf_cookie_name):
        response.delete_cookie(
            key=cookie_name,
            path="/",
            secure=settings.session_cookie_secure,
            samesite=settings.session_cookie_samesite,
        )


@router.post("/login", response_model=UserResponse, summary="Autenticar e criar sessão")
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    key = login_guard.build_key(
        payload.email,
        request.client.host if request.client else None,
    )
    if not login_guard.ensure_allowed(key):
        raise RateLimitError()

    user = authenticate_user(db, payload.email, payload.password)
    if user is None:
        login_guard.record_failure(
            key,
            max_attempts=settings.login_max_attempts,
            lockout_minutes=settings.login_lockout_minutes,
        )
        raise AuthenticationError("E-mail ou senha inválidos.")

    login_guard.clear(key)
    issued = create_session(db, user.id, settings)
    set_session_cookies(response, issued, settings)
    return user


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Encerrar sessão e revogar cookies",
)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> None:
    session = get_active_session(db, request.cookies.get(settings.session_cookie_name))
    if session is not None:
        revoke_session(db, session)
    delete_session_cookies(response, settings)
    response.status_code = status.HTTP_204_NO_CONTENT


@router.get("/me", response_model=CurrentUserResponse, summary="Consultar usuário atual")
def me(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    scope: TenantScope = Depends(get_tenant_scope),
) -> CurrentUserResponse:
    user = scope.get(db, User, current_user.id)
    company = db.get(Company, user.company_id)
    if company is None:
        raise NotFoundError("Empresa não encontrada.")

    return CurrentUserResponse(
        **UserResponse.model_validate(user).model_dump(),
        company=CompanySummary.model_validate(company),
    )
