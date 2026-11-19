"""Hash e verificação de senhas com Argon2id."""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from argon2.low_level import Type

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# Parâmetros alinhados às recomendações da OWASP para Argon2id.
_password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
    type=Type.ID,
)


def hash_password(password: str) -> str:
    """Gera o hash de uma senha válida."""

    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        raise ValueError(
            f"A senha deve ter entre {MIN_PASSWORD_LENGTH} e "
            f"{MAX_PASSWORD_LENGTH} caracteres."
        )
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica a senha sem revelar detalhes do hash armazenado."""

    try:
        return _password_hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError, TypeError, ValueError):
        return False
