from uuid import uuid4

import pytest
from sqlalchemy import UniqueConstraint
from sqlalchemy.exc import IntegrityError

from app.core.permissions import UserRole
from app.models import Company, User


def test_company_requires_legal_name(db_session):
    db_session.add(Company())

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_email_is_unique_globally(db_session, users):
    ana, carlos = users
    duplicate = User(
        company_id=carlos.company_id,
        name="E-mail repetido",
        email=ana.email,
        password_hash="hash-teste",
        role=UserRole.ATTENDANT,
    )
    db_session.add(duplicate)

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_requires_company(db_session):
    db_session.add(
        User(
            name="Sem empresa",
            email="sem-empresa@example.com",
            password_hash="hash-teste",
            role=UserRole.ATTENDANT,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_cannot_reference_unknown_company(db_session):
    db_session.add(
        User(
            company_id=uuid4(),
            name="Empresa inexistente",
            email="empresa-inexistente@example.com",
            password_hash="hash-teste",
            role=UserRole.ATTENDANT,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_role_is_persisted_as_value(db_session, users):
    _, carlos = users

    db_session.refresh(carlos)

    assert carlos.role == UserRole.TECHNICIAN


def test_user_company_relationship_uses_own_company(companies, users):
    alpha, beta = companies
    ana, carlos = users

    assert ana.company.id == alpha.id
    assert carlos.company.id == beta.id


def test_users_have_composite_company_scope_unique_constraint():
    constraint = next(
        item
        for item in User.__table__.constraints
        if isinstance(item, UniqueConstraint)
        and item.name == "uq_users_company_id_id"
    )

    assert {column.name for column in constraint.columns} == {"company_id", "id"}
