from typing import Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationError
from app.core.security import get_current_company_id


class TenantScope:
    """Escopo de empresa obtido da identidade autenticada.

    Nenhum consumidor desta classe deve receber `company_id` do cliente HTTP.
    """

    def __init__(self, company_id: UUID) -> None:
        self.company_id = company_id

    def select(self, model: type, *columns: Any):
        selected: tuple[Any, ...] = columns or (model,)
        return select(*selected).where(model.company_id == self.company_id)

    def filter(self, query, model: type):
        return query.where(model.company_id == self.company_id)

    def get(self, db: Session, model: type, object_id: UUID):
        obj = db.get(model, object_id)
        if obj is None or getattr(obj, "company_id", None) != self.company_id:
            raise NotFoundError()
        return obj

    def ensure_same_company(self, company_id: UUID | None, field_name: str) -> None:
        if company_id is None or company_id != self.company_id:
            raise ValidationError(fields={field_name: "Registro não encontrado."})


def get_tenant_scope(company_id: UUID = Depends(get_current_company_id)) -> TenantScope:
    return TenantScope(company_id)
