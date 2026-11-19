"""Regras de negócio do gerenciamento de usuários da empresa autenticada."""

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ConflictError
from app.core.password import hash_password
from app.core.permissions import UserRole
from app.core.tenant import TenantScope
from app.models import User
from app.schemas.user import UserCreate, UserList, UserResponse, UserStatusUpdate, UserUpdate


def email_is_taken(db: Session, email: str, *, exclude_user_id=None) -> bool:
    statement = select(User.id).where(func.lower(User.email) == email.strip().lower())
    if exclude_user_id is not None:
        statement = statement.where(User.id != exclude_user_id)
    return db.scalars(statement).first() is not None


def create_user(db: Session, scope: TenantScope, payload: UserCreate) -> User:
    if email_is_taken(db, payload.email):
        raise ConflictError("E-mail já cadastrado.")

    user = User(
        company_id=scope.company_id,
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("E-mail já cadastrado.") from None
    db.refresh(user)
    return user


def list_users(
    db: Session,
    scope: TenantScope,
    *,
    page: int,
    page_size: int,
    search: str | None = None,
    role: UserRole | None = None,
    is_active: bool | None = None,
) -> UserList:
    statement = scope.select(User)
    if search:
        pattern = f"%{search.strip().lower()}%"
        statement = statement.where(
            or_(
                func.lower(User.name).like(pattern),
                func.lower(User.email).like(pattern),
            )
        )
    if role is not None:
        statement = statement.where(User.role == role)
    if is_active is not None:
        statement = statement.where(User.is_active.is_(is_active))

    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    users = db.scalars(
        statement.order_by(User.name, User.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return UserList(
        items=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_user(db: Session, scope: TenantScope, user_id) -> User:
    return scope.get(db, User, user_id)


def update_user(db: Session, scope: TenantScope, user_id, payload: UserUpdate) -> User:
    user = scope.get(db, User, user_id)
    changes = payload.model_dump(exclude_unset=True)

    if "email" in changes and email_is_taken(db, changes["email"], exclude_user_id=user.id):
        raise ConflictError("E-mail já cadastrado.")

    if "password" in changes and changes["password"] is not None:
        user.password_hash = hash_password(changes["password"])

    for field in ("name", "email", "role"):
        if field in changes and changes[field] is not None:
            setattr(user, field, changes[field])

    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("E-mail já cadastrado.") from None
    db.refresh(user)
    return user


def set_user_status(
    db: Session,
    scope: TenantScope,
    user_id,
    payload: UserStatusUpdate,
) -> User:
    user = scope.get(db, User, user_id)
    user.is_active = payload.is_active
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
