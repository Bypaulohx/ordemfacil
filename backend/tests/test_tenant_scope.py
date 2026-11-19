from uuid import UUID, uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.errors import NotFoundError, ValidationError, register_exception_handlers
from app.core.permissions import UserRole
from app.core.security import CurrentUser, get_current_company_id, get_current_user
from app.core.tenant import TenantScope
from app.models import User


@pytest.fixture
def scope(companies):
    alpha, _ = companies
    return TenantScope(alpha.id)


def test_scope_get_returns_only_records_from_own_company(db_session, scope, users):
    ana, carlos = users

    assert scope.get(db_session, User, ana.id) is ana

    with pytest.raises(NotFoundError):
        scope.get(db_session, User, carlos.id)


def test_scope_select_always_filters_by_company(db_session, scope, users):
    ana, carlos = users

    found = db_session.scalars(scope.select(User)).all()

    assert found == [ana]
    assert carlos not in found


def test_scope_ensures_related_ids_belong_to_the_same_company(scope, users):
    ana, carlos = users

    scope.ensure_same_company(ana.company_id, "company_id")

    with pytest.raises(ValidationError) as error:
        scope.ensure_same_company(carlos.company_id, "company_id")

    assert error.value.fields == {"company_id": "Registro não encontrado."}


def test_company_id_comes_from_authenticated_identity(companies):
    alpha, beta = companies
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/contexto")
    def contexto(company_id: UUID = Depends(get_current_company_id)):
        return {"company_id": str(company_id)}

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(),
        company_id=alpha.id,
        role=UserRole.ADMIN,
    )

    client = TestClient(app)
    response = client.get("/contexto")
    assert response.status_code == 200
    assert response.json() == {"company_id": str(alpha.id)}

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        id=uuid4(),
        company_id=beta.id,
        role=UserRole.ADMIN,
        is_active=False,
    )
    response = client.get("/contexto")
    assert response.status_code == 401
