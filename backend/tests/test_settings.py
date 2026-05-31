from app.settings import get_settings, load_settings_from_env


def test_settings_defaults(monkeypatch) -> None:
    monkeypatch.delenv("MODAL_IMG_APP_ENV", raising=False)
    monkeypatch.delenv("MODAL_IMG_REDIS_URL", raising=False)
    monkeypatch.delenv("MODAL_IMG_POSTGRES_DSN", raising=False)
    monkeypatch.delenv("MODAL_IMG_GENERATION_QUEUE_KEY", raising=False)
    monkeypatch.delenv("MODAL_IMG_FRONTEND_ORIGIN", raising=False)

    settings = load_settings_from_env()

    assert settings.app_env == "development"
    assert settings.redis_url == "redis://127.0.0.1:6379/0"
    assert (
        settings.postgres_dsn
        == "postgresql://modal_img:modal_img@127.0.0.1:5432/modal_img"
    )
    assert settings.generation_queue_key == "modal-img:generation-jobs"
    assert settings.frontend_origin == "http://127.0.0.1:4173"


def test_settings_read_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv("MODAL_IMG_APP_ENV", "test")
    monkeypatch.setenv("MODAL_IMG_REDIS_URL", "redis://redis.internal:6380/2")
    monkeypatch.setenv(
        "MODAL_IMG_POSTGRES_DSN",
        "postgresql://worker:secret@postgres.internal:5433/modal_img_test",
    )
    monkeypatch.setenv(
        "MODAL_IMG_GENERATION_QUEUE_KEY",
        "modal-img:test-generation-jobs",
    )
    monkeypatch.setenv(
        "MODAL_IMG_FRONTEND_ORIGIN",
        "http://frontend.internal:8080",
    )

    settings = load_settings_from_env()

    assert settings.app_env == "test"
    assert settings.redis_url == "redis://redis.internal:6380/2"
    assert (
        settings.postgres_dsn
        == "postgresql://worker:secret@postgres.internal:5433/modal_img_test"
    )
    assert settings.generation_queue_key == "modal-img:test-generation-jobs"
    assert settings.frontend_origin == "http://frontend.internal:8080"


def test_get_settings_is_cached() -> None:
    get_settings.cache_clear()
    settings_one = get_settings()
    settings_two = get_settings()

    assert settings_one is settings_two

    get_settings.cache_clear()
