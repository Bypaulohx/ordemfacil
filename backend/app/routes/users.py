"""Endpoints de gerenciamento de usuários da empresa autenticada."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.permissions import UserRole
from app.core.security import require_admin
from app.core.tenant import TenantScope, get_tenant_scope
from app.database.session import get_db
from app.models import User
from app.schemas.user import (
    UserCreate,
    UserList,
    UserResponse,
    UserStatusUpdate,
    UserUpdate,
)
from app.services import users as user_service

router = APIRouter(
    prefix="/users",
    tags=["usuários"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=UserList, summary="Listar usuários da empresa")
def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=150),
    role: UserRole | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    scope: TenantScope = Depends(get_tenant_scope),
) -> UserList:
    return user_service.list_users(
        db,
        scope,
        page=page,
        page_size=page_size,
        search=search,
        role=role,
        is_active=is_active,
    )


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar usuário na empresa autenticada",
)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    scope: TenantScope = Depends(get_tenant_scope),
) -> User:
    return user_service.create_user(db, scope, payload)


@router.get("/{user_id}", response_model=UserResponse, summary="Consultar usuário")
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    scope: TenantScope = Depends(get_tenant_scope),
) -> User:
    return user_service.get_user(db, scope, user_id)


@router.put("/{user_id}", response_model=UserResponse, summary="Atualizar usuário")
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    scope: TenantScope = Depends(get_tenant_scope),
) -> User:
    return user_service.update_user(db, scope, user_id, payload)


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
    summary="Ativar ou inativar usuário",
)
def set_user_status(
    user_id: UUID,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    scope: TenantScope = Depends(get_tenant_scope),
) -> User:
    return user_service.set_user_status(db, scope, user_id, payload)
