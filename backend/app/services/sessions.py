"""Criação, consulta e revogação de sessões server-side."""

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.session import UserSession

SESSION_TOKEN_BYTES = 32
CSRF_TOKEN_BYTES = 32


@dataclass(frozen=True)
class IssuedSession:
    """Dados retornados pela emissão: segredos apenas no cookie/resposta."""

    token: str
    csrf_token: str
    session: UserSession


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_token(size: int) -> str:
    return secrets.token_urlsafe(size)


def hash_token(token: str) -> str:
    """O token é aleatório de 256 bits; SHA-256 é suficiente para o registro."""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(db: Session, user_id: UUID, settings: Settings) -> IssuedSession:
    token = generate_token(SESSION_TOKEN_BYTES)
    csrf_token = generate_token(CSRF_TOKEN_BYTES)
    session = UserSession(
        user_id=user_id,
        token_hash=hash_token(token),
        csrf_token_hash=hash_token(csrf_token),
        expires_at=utc_now() + timedelta(minutes=settings.session_expire_minutes),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return IssuedSession(token=token, csrf_token=csrf_token, session=session)


def get_active_session(
    db: Session,
    token: str | None,
    *,
    now: datetime | None = None,
) -> UserSession | None:
    if not token:
        return None
    statement = select(UserSession).where(
        UserSession.token_hash == hash_token(token),
        UserSession.revoked_at.is_(None),
        UserSession.expires_at > (now or utc_now()),
    )
    return db.scalars(statement).first()


def revoke_session(db: Session, session: UserSession) -> None:
    session.revoked_at = utc_now()
    db.add(session)
    db.commit()
