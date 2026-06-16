import json

from app.services.settings_service import SettingsService
from config.settings import DEFAULT_APP_SETTINGS


def test_load_creates_default_settings_file(tmp_path):
    settings_path = tmp_path / "config" / "app_settings.json"
    service = SettingsService(settings_path, tmp_path / "logs" / "error.log")

    settings = service.load()

    assert settings == DEFAULT_APP_SETTINGS
    assert settings_path.exists()
    assert json.loads(settings_path.read_text(encoding="utf-8")) == DEFAULT_APP_SETTINGS


def test_save_and_load_settings(tmp_path):
    settings_path = tmp_path / "config" / "app_settings.json"
    service = SettingsService(settings_path, tmp_path / "logs" / "error.log")
    settings = service.create_default_settings()
    settings["license_id"] = "LIC-TEST-001"
    settings["device_role"] = "master"

    service.save(settings)

    assert service.load()["device_role"] == "master"


def test_corrupted_settings_file_is_backed_up_and_recreated(tmp_path):
    settings_path = tmp_path / "config" / "app_settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text("{ invalid json", encoding="utf-8")

    service = SettingsService(settings_path, tmp_path / "logs" / "error.log")
    settings = service.load()

    backups = list(settings_path.parent.glob("app_settings_broken_*.json"))
    assert settings == DEFAULT_APP_SETTINGS
    assert len(backups) == 1
    assert settings_path.exists()


def test_invalid_settings_structure_is_backed_up_and_recreated(tmp_path):
    settings_path = tmp_path / "config" / "app_settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text('{"schema_version": 999}', encoding="utf-8")

    service = SettingsService(settings_path, tmp_path / "logs" / "error.log")
    settings = service.load()

    backups = list(settings_path.parent.glob("app_settings_broken_*.json"))
    assert settings == DEFAULT_APP_SETTINGS
    assert len(backups) == 1
