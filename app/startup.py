from __future__ import annotations

from app.services.license_settings_service import (
    LicenseSettingsValidationError,
    validate_license_device_settings,
)
from app.services.settings_service import SettingsService
from app.windows.license_settings_window import LicenseSettingsWindow
from app.windows.main_menu_window import MainMenuWindow


def has_valid_license_device_settings(settings: dict) -> bool:
    try:
        validate_license_device_settings(
            settings.get("license_id", ""),
            settings.get("device_role", ""),
        )
    except (AttributeError, LicenseSettingsValidationError):
        return False
    return True


class StartupController:
    def __init__(
        self,
        settings_service: SettingsService | None = None,
        main_window_class: type[MainMenuWindow] = MainMenuWindow,
        license_window_class: type[LicenseSettingsWindow] = LicenseSettingsWindow,
    ) -> None:
        self.settings_service = settings_service or SettingsService()
        self.main_window_class = main_window_class
        self.license_window_class = license_window_class
        self.current_window = None

    def show_initial_window(self):
        settings = self.settings_service.load()
        if has_valid_license_device_settings(settings):
            return self.show_main_window(settings)
        return self.show_license_settings_window(settings)

    def show_main_window(self, settings: dict | None = None):
        self.current_window = self.main_window_class(
            settings=settings,
            settings_service=self.settings_service,
        )
        self.current_window.show()
        return self.current_window

    def show_license_settings_window(self, settings: dict | None = None):
        self.current_window = self.license_window_class(
            settings_service=self.settings_service,
            initial_settings=settings,
            on_saved=self.show_main_window,
        )
        self.current_window.show()
        return self.current_window
