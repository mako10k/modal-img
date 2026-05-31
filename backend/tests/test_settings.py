from app.settings import get_settings, load_settings_from_env


def test_settings_defaults(monkeypatch) -> None:
    monkeypatch.delenv("MODAL_IMG_APP_ENV", raising=False)
    monkeypatch.delenv("MODAL_IMG_MODAL_APP_NAME", raising=False)
    monkeypatch.delenv(
        "MODAL_IMG_MODAL_TEXT_TO_IMAGE_FUNCTION_NAME",
        raising=False,
    )
    monkeypatch.delenv("MODAL_IMG_MODAL_ENVIRONMENT_NAME", raising=False)
    monkeypatch.delenv("MODAL_IMG_COMFYUI_BASE_URL", raising=False)
    monkeypatch.delenv("MODAL_IMG_COMFYUI_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv(
        "MODAL_IMG_COMFYUI_HEALTH_TIMEOUT_SECONDS",
        raising=False,
    )
    monkeypatch.delenv(
        "MODAL_IMG_DEPENDENCY_HEALTH_TIMEOUT_SECONDS",
        raising=False,
    )
    monkeypatch.delenv("MODAL_IMG_COMFYUI_CHECKPOINT", raising=False)
    monkeypatch.delenv("MODAL_IMG_COMFYUI_OUTPUT_PREFIX", raising=False)
    monkeypatch.delenv("MODAL_IMG_REDIS_URL", raising=False)
    monkeypatch.delenv("MODAL_IMG_POSTGRES_DSN", raising=False)
    monkeypatch.delenv(
        "MODAL_IMG_POSTGRES_CONNECT_TIMEOUT_SECONDS",
        raising=False,
    )
    monkeypatch.delenv("MODAL_IMG_REDIS_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("MODAL_IMG_GENERATION_QUEUE_KEY", raising=False)
    monkeypatch.delenv("MODAL_IMG_FRONTEND_ORIGIN", raising=False)

    settings = load_settings_from_env()

    assert settings.app_env == "development"
    assert settings.modal_app_name == "modal-img-execution"
    assert settings.modal_text_to_image_function_name == "submit_text_to_image"
    assert settings.modal_environment_name is None
    assert settings.comfyui_base_url == "http://127.0.0.1:8188"
    assert settings.comfyui_timeout_seconds == 30.0
    assert settings.comfyui_health_timeout_seconds == 2.0
    assert settings.dependency_health_timeout_seconds == 2.0
    assert settings.comfyui_checkpoint == "sd_xl_base_1.0.safetensors"
    assert settings.comfyui_output_prefix == "modal-img"
    assert settings.redis_url == "redis://127.0.0.1:6379/0"
    assert (
        settings.postgres_dsn
        == "postgresql://modal_img:modal_img@127.0.0.1:5432/modal_img"
    )
    assert settings.postgres_connect_timeout_seconds == 5.0
    assert settings.redis_timeout_seconds == 5.0
    assert settings.generation_queue_key == "modal-img:generation-jobs"
    assert settings.frontend_origin == "http://127.0.0.1:43173"


def test_settings_read_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv("MODAL_IMG_APP_ENV", "test")
    monkeypatch.setenv("MODAL_IMG_MODAL_APP_NAME", "modal-img-execution-test")
    monkeypatch.setenv(
        "MODAL_IMG_MODAL_TEXT_TO_IMAGE_FUNCTION_NAME",
        "submit_text_to_image_test",
    )
    monkeypatch.setenv("MODAL_IMG_MODAL_ENVIRONMENT_NAME", "dev")
    monkeypatch.setenv(
        "MODAL_IMG_COMFYUI_BASE_URL",
        "http://comfyui.internal:8188",
    )
    monkeypatch.setenv("MODAL_IMG_COMFYUI_TIMEOUT_SECONDS", "45.5")
    monkeypatch.setenv("MODAL_IMG_COMFYUI_HEALTH_TIMEOUT_SECONDS", "3.5")
    monkeypatch.setenv("MODAL_IMG_DEPENDENCY_HEALTH_TIMEOUT_SECONDS", "1.5")
    monkeypatch.setenv(
        "MODAL_IMG_COMFYUI_CHECKPOINT",
        "quality-model.safetensors",
    )
    monkeypatch.setenv("MODAL_IMG_COMFYUI_OUTPUT_PREFIX", "modal-img-test")
    monkeypatch.setenv("MODAL_IMG_REDIS_URL", "redis://redis.internal:6380/2")
    monkeypatch.setenv(
        "MODAL_IMG_POSTGRES_DSN",
        "postgresql://worker:secret@postgres.internal:5433/modal_img_test",
    )
    monkeypatch.setenv(
        "MODAL_IMG_POSTGRES_CONNECT_TIMEOUT_SECONDS",
        "6.5",
    )
    monkeypatch.setenv("MODAL_IMG_REDIS_TIMEOUT_SECONDS", "4.5")
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
    assert settings.modal_app_name == "modal-img-execution-test"
    assert settings.modal_text_to_image_function_name == (
        "submit_text_to_image_test"
    )
    assert settings.modal_environment_name == "dev"
    assert settings.comfyui_base_url == "http://comfyui.internal:8188"
    assert settings.comfyui_timeout_seconds == 45.5
    assert settings.comfyui_health_timeout_seconds == 3.5
    assert settings.dependency_health_timeout_seconds == 1.5
    assert settings.comfyui_checkpoint == "quality-model.safetensors"
    assert settings.comfyui_output_prefix == "modal-img-test"
    assert settings.redis_url == "redis://redis.internal:6380/2"
    assert (
        settings.postgres_dsn
        == "postgresql://worker:secret@postgres.internal:5433/modal_img_test"
    )
    assert settings.postgres_connect_timeout_seconds == 6.5
    assert settings.redis_timeout_seconds == 4.5
    assert settings.generation_queue_key == "modal-img:test-generation-jobs"
    assert settings.frontend_origin == "http://frontend.internal:8080"


def test_settings_treat_empty_modal_environment_as_unset(
    monkeypatch,
) -> None:
    monkeypatch.setenv("MODAL_IMG_MODAL_ENVIRONMENT_NAME", "   ")

    settings = load_settings_from_env()

    assert settings.modal_environment_name is None


def test_get_settings_is_cached() -> None:
    get_settings.cache_clear()
    settings_one = get_settings()
    settings_two = get_settings()

    assert settings_one is settings_two

    get_settings.cache_clear()
