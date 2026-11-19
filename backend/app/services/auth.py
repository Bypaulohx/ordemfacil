"""Regras de autenticação de usuários."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.password import verify_password
from app.models import Company, User


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Retorna o usuário somente quando credenciais e situação são válidas."""

    statement = select(User).where(func.lower(User.email) == email.strip().lower())
    user = db.scalars(statement).first()
    if user is None or not user.is_active:
        return None

    company = db.get(Company, user.company_id)
    if company is None or not company.is_active:
        return None

    if not verify_password(password, user.password_hash):
        return None
    return user
