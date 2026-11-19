"""Limitação de tentativas de login (medida de abuso em processo único)."""

import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class _AttemptBucket:
    failures: int = 0
    window_started_at: datetime | None = None
    locked_until: datetime | None = None


class LoginGuard:
    """Controla tentativas por credencial informada e origem da requisição.

    O estado é em memória: em instalações com múltiplos processos, substituir
    por um store compartilhado (por exemplo, Redis) sem alterar os chamadores.
    """

    def __init__(self) -> None:
        self._buckets: dict[tuple[str, str], _AttemptBucket] = {}
        self._lock = threading.Lock()

    @staticmethod
    def build_key(email: str, client_host: str | None) -> tuple[str, str]:
        return email.strip().lower(), client_host or "desconhecido"

    def ensure_allowed(self, key: tuple[str, str], *, now: datetime | None = None) -> bool:
        current = now or datetime.now(timezone.utc)
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                return True
            if bucket.locked_until is not None and current < bucket.locked_until:
                return False
            if bucket.locked_until is not None:
                self._buckets.pop(key, None)
            return True

    def record_failure(
        self,
        key: tuple[str, str],
        *,
        max_attempts: int,
        lockout_minutes: int,
        now: datetime | None = None,
    ) -> None:
        current = now or datetime.now(timezone.utc)
        with self._lock:
            bucket = self._buckets.setdefault(key, _AttemptBucket())
            if (
                bucket.window_started_at is None
                or current - bucket.window_started_at >= timedelta(minutes=lockout_minutes)
            ):
                bucket.failures = 0
                bucket.window_started_at = current
                bucket.locked_until = None
            bucket.failures += 1
            if bucket.failures >= max_attempts:
                bucket.locked_until = current + timedelta(minutes=lockout_minutes)

    def clear(self, key: tuple[str, str]) -> None:
        with self._lock:
            self._buckets.pop(key, None)

    def clear_all(self) -> None:
        with self._lock:
            self._buckets.clear()


login_guard = LoginGuard()
