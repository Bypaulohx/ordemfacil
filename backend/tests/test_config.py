from app.core.config import DEVELOPMENT_SECRET_PLACEHOLDER, Settings, get_settings


def test_default_settings_are_development_friendly():
    settings = Settings(_env_file=None)

    assert settings.app_name == "OrdemFacil"
    assert settings.app_env == "development"
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.session_cookie_name == "ordemfacil_session"
    assert settings.csrf_cookie_name == "ordemfacil_csrf"
    assert settings.login_max_attempts == 5
    assert settings.login_lockout_minutes == 15


def test_cors_origins_are_parsed_from_csv():
    settings = Settings(
        cors_origins="https://alfa.example, https://beta.example",
        _env_file=None,
    )

    assert settings.cors_origins == [
        "https://alfa.example",
        "https://beta.example",
    ]


def test_production_requires_secure_settings():
    common = {
        "app_env": "production",
        "app_debug": False,
        "secret_key": "chave-ficticia-longa",
        "session_cookie_secure": True,
        "_env_file": None,
    }

    assert Settings(**common).app_env == "production"

    for override in (
        {"app_debug": True},
        {"secret_key": DEVELOPMENT_SECRET_PLACEHOLDER},
        {"session_cookie_secure": False},
    ):
        try:
            Settings(**{**common, **override})
        except ValueError:
            continue
        raise AssertionError(f"Configuração inválida aceita: {override}")


def test_login_attempt_limits_must_be_positive():
    for field in ("login_max_attempts", "login_lockout_minutes"):
        try:
            Settings(**{field: 0, "_env_file": None})
        except ValueError:
            continue
        raise AssertionError(f"Configuração inválida aceita: {field}")


def test_get_settings_is_cached():
    get_settings.cache_clear()
    try:
        assert get_settings() is get_settings()
    finally:
        get_settings.cache_clear()
