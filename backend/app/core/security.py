"""Identidade autenticada, autorização por perfil e validação de CSRF."""

import secrets
from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import AuthenticationError, AuthorizationError, CSRFError
from app.core.permissions import UserRole
from app.database.session import get_db
from app.models import Company, User
from app.services.sessions import (
    get_active_session,
    hash_token,
)

UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


@dataclass(frozen=True)
class CurrentUser:
    """Identidade autenticada disponível para as dependências da API."""

    id: UUID
    company_id: UUID
    role: UserRole
    is_active: bool = True


def _validate_csrf(request: Request, settings: Settings, csrf_token_hash: str) -> None:
    cookie_token = request.cookies.get(settings.csrf_cookie_name)
    header_token = request.headers.get("X-CSRF-Token")

    if not cookie_token or not header_token:
        raise CSRFError()
    if not secrets.compare_digest(cookie_token, header_token):
        raise CSRFError()
    if not secrets.compare_digest(hash_token(header_token), csrf_token_hash):
        raise CSRFError()


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    """Recupera a identidade da sessão e valida CSRF em operações de escrita."""

    session = get_active_session(db, request.cookies.get(settings.session_cookie_name))
    if session is None:
        raise AuthenticationError()

    user = db.get(User, session.user_id)
    if user is None or not user.is_active:
        raise AuthenticationError()

    company = db.get(Company, user.company_id)
    if company is None or not company.is_active:
        raise AuthenticationError()

    if request.method in UNSAFE_METHODS:
        _validate_csrf(request, settings, session.csrf_token_hash)

    return CurrentUser(
        id=user.id,
        company_id=user.company_id,
        role=user.role,
        is_active=user.is_active,
    )


def get_current_company_id(current_user: CurrentUser = Depends(get_current_user)) -> UUID:
    if not current_user.is_active:
        raise AuthenticationError("Usuário inativo.")
    return current_user.company_id


def require_roles(*roles: UserRole) -> Callable[..., CurrentUser]:
    """Cria dependência que restringe o endpoint aos perfis informados."""

    def check_role(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in roles:
            raise AuthorizationError()
        return current_user

    return check_role


require_admin = require_roles(UserRole.ADMIN)
require_admin_or_attendant = require_roles(UserRole.ADMIN, UserRole.ATTENDANT)
