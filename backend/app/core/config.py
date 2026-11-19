from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_SECRET_PLACEHOLDER = "development-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "OrdemFacil"
    app_env: Literal["development", "test", "production"] = "development"
    app_debug: bool = True
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+psycopg://usuario:senha@localhost:5432/ordemfacil"

    secret_key: str = DEVELOPMENT_SECRET_PLACEHOLDER
    session_expire_minutes: int = 480
    session_cookie_name: str = "ordemfacil_session"
    session_cookie_secure: bool = False
    session_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    csrf_cookie_name: str = "ordemfacil_csrf"
    login_max_attempts: int = Field(default=5, ge=1)
    login_lockout_minutes: int = Field(default=15, ge=1)

    cors_origins: list[str] = [
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def enforce_production_rules(self) -> "Settings":
        if self.app_env == "production":
            if self.app_debug:
                raise ValueError("APP_DEBUG deve ser false em produção.")
            if self.secret_key == DEVELOPMENT_SECRET_PLACEHOLDER:
                raise ValueError("SECRET_KEY deve ser definida em produção.")
            if not self.session_cookie_secure:
                raise ValueError("SESSION_COOKIE_SECURE deve ser true em produção.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
