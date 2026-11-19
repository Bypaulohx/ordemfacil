from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.permissions import UserRole
from app.database.base import BaseModel

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.session import UserSession


def _user_role_values(enum_class: type[UserRole]) -> list[str]:
    return [member.value for member in enum_class]


class User(BaseModel):
    __tablename__ = "users"

    company_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "companies.id",
            ondelete="RESTRICT",
            name="fk_users_company_id_companies",
        ),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            values_callable=_user_role_values,
        ),
        nullable=False,
        default=UserRole.ATTENDANT,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )

    company: Mapped["Company"] = relationship(back_populates="users")
    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint("company_id", "id", name="uq_users_company_id_id"),
        Index("ix_users_company_id_email", "company_id", "email", unique=True),
    )
