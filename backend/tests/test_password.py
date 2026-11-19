import pytest

from app.core.password import hash_password, verify_password


def test_password_hash_uses_argon2id_and_is_not_plaintext():
    hashed = hash_password("Senha@123")

    assert hashed != "Senha@123"
    assert hashed.startswith("$argon2id$")


def test_password_verification():
    hashed = hash_password("Senha@123")

    assert verify_password("Senha@123", hashed)
    assert not verify_password("senha-errada", hashed)


def test_invalid_stored_hash_does_not_raise():
    assert not verify_password("Senha@123", "hash-invalido")


def test_short_passwords_are_rejected_by_hasher():
    with pytest.raises(ValueError):
        hash_password("curta")
