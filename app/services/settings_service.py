from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import shutil

from app.utils.logging_config import configure_error_logging, log_exception
from app.utils.paths import project_path
from config.settings import (
    APP_SETTINGS_RELATIVE_PATH,
    DEFAULT_APP_SETTINGS,
    VALID_DEVICE_ROLES,
)


class SettingsService:
    def __init__(
        self,
        settings_path: Path | None = None,
        log_file: Path | None = None,
    ) -> None:
        self.settings_path = settings_path or project_path(*APP_SETTINGS_RELATIVE_PATH)
        self.logger = configure_error_logging(log_file)

    def load(self) -> dict:
        if not self.settings_path.exists():
            settings = self.create_default_settings()
            self.save(settings)
            return settings

        try:
            with self.settings_path.open("r", encoding="utf-8") as settings_file:
                settings = json.load(settings_file)
            self._validate_settings(settings)
            return settings
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            self._backup_broken_settings(exc)
            settings = self.create_default_settings()
            self.save(settings)
            return settings

    def save(self, settings: dict) -> None:
        try:
            self._validate_settings(settings)
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            with self.settings_path.open("w", encoding="utf-8") as settings_file:
                json.dump(settings, settings_file, ensure_ascii=False, indent=2)
                settings_file.write("\n")
        except Exception as exc:
            log_exception("settings_save", exc, self.settings_path, self.logger)
            raise

    def create_default_settings(self) -> dict:
        return deepcopy(DEFAULT_APP_SETTINGS)

    def _backup_broken_settings(self, exception: Exception) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.settings_path.with_name(
            f"app_settings_broken_{timestamp}.json"
        )
        try:
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            if self.settings_path.exists():
                shutil.move(str(self.settings_path), str(backup_path))
            log_exception("settings_load", exception, backup_path, self.logger)
        except Exception as backup_exception:
            log_exception(
                "settings_broken_backup",
                backup_exception,
                self.settings_path,
                self.logger,
            )
            raise

    def _validate_settings(self, settings: dict) -> None:
        if not isinstance(settings, dict):
            raise ValueError("settings must be a JSON object")

        required_keys = set(DEFAULT_APP_SETTINGS.keys())
        missing_keys = required_keys.difference(settings.keys())
        if missing_keys:
            raise ValueError("settings are missing required keys")

        if settings["schema_version"] != DEFAULT_APP_SETTINGS["schema_version"]:
            raise ValueError("unsupported settings schema_version")

        if not isinstance(settings["license_id"], str):
            raise ValueError("license_id must be a string")

        if settings["device_role"] not in VALID_DEVICE_ROLES:
            raise ValueError("device_role is invalid")

        for key in ("last_mcd_export_dir", "last_mcd_import_dir"):
            if not isinstance(settings[key], str):
                raise ValueError(f"{key} must be a string")

        self._validate_display_settings(settings["display_settings"])
        self._validate_output_settings(settings["output_settings"])

    def _validate_display_settings(self, display_settings: dict) -> None:
        if not isinstance(display_settings, dict):
            raise ValueError("display_settings must be a JSON object")

        defaults = DEFAULT_APP_SETTINGS["display_settings"]
        missing_keys = set(defaults.keys()).difference(display_settings.keys())
        if missing_keys:
            raise ValueError("display_settings are missing required keys")

        if not isinstance(display_settings["always_on_top"], bool):
            raise ValueError("always_on_top must be a boolean")
        if not isinstance(display_settings["transparent_mode"], bool):
            raise ValueError("transparent_mode must be a boolean")
        if not isinstance(display_settings["font_size"], int):
            raise ValueError("font_size must be an integer")
        if not isinstance(display_settings["text_color"], str):
            raise ValueError("text_color must be a string")
        if not isinstance(display_settings["background_color"], str):
            raise ValueError("background_color must be a string")
        if not isinstance(display_settings["opacity"], (int, float)):
            raise ValueError("opacity must be a number")

    def _validate_output_settings(self, output_settings: dict) -> None:
        if not isinstance(output_settings, dict):
            raise ValueError("output_settings must be a JSON object")

        defaults = DEFAULT_APP_SETTINGS["output_settings"]
        missing_keys = set(defaults.keys()).difference(output_settings.keys())
        if missing_keys:
            raise ValueError("output_settings are missing required keys")

        if not isinstance(output_settings["last_output_dir"], str):
            raise ValueError("last_output_dir must be a string")
        if output_settings["default_format"] != "csv":
            raise ValueError("default_format must be csv")
