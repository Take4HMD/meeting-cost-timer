from __future__ import annotations

from app.services.license_settings_service import (
    LicenseSettingsValidationError,
    validate_license_device_settings,
)
from app.services.settings_service import SettingsService
from app.windows.base_window import UiWindow
from app.windows.display_settings_window import DisplaySettingsWindow
from app.windows.license_settings_window import LicenseSettingsWindow
from app.windows.master_menu_window import MasterMenuWindow
from app.windows.meeting_start_settings_window import MeetingStartSettingsWindow


DEVICE_ROLE_LABELS = {
    "master": "親機",
    "viewer": "子機",
}
APP_VERSION_TEXT = "Ver.1.0.0"


class MainMenuWindow(UiWindow):
    ui_file_name = "main_menu.ui"

    def __init__(
        self,
        settings: dict | None = None,
        settings_service: SettingsService | None = None,
        destination_window_classes: dict[str, type] | None = None,
    ) -> None:
        super().__init__()
        self.settings = settings or {}
        self.settings_service = settings_service or SettingsService()
        self.destination_window_classes = destination_window_classes or {
            "meeting_start": MeetingStartSettingsWindow,
            "master_menu": MasterMenuWindow,
            "display_settings": DisplaySettingsWindow,
            "license_settings": LicenseSettingsWindow,
        }
        self.opened_windows = []

        self.startMeetingButton.clicked.connect(
            lambda: self.open_destination_window("meeting_start")
        )
        self.masterMenuButton.clicked.connect(
            lambda: self.open_destination_window("master_menu")
        )
        self.displaySettingsButton.clicked.connect(
            lambda: self.open_destination_window("display_settings")
        )
        self.licenseSettingsButton.clicked.connect(self.open_license_settings_window)
        self.exitButton.clicked.connect(self.close)
        self.apply_settings(self.settings)

    def apply_settings(self, settings: dict) -> None:
        self.settings = settings
        device_role = settings.get("device_role", "")
        device_role_text = DEVICE_ROLE_LABELS.get(device_role, "未設定")
        license_status_text = self._license_status_text(settings)

        self.deviceRoleLabel.setText(f"端末種別: {device_role_text}")
        self.licenseStatusLabel.setText(f"ライセンス状態: {license_status_text}")
        self.appVersionLabel.setText(APP_VERSION_TEXT)

    def open_destination_window(self, destination: str):
        window_class = self.destination_window_classes[destination]
        if destination == "meeting_start":
            window = window_class(
                settings=self.settings,
                settings_service=self.settings_service,
            )
        elif destination == "master_menu":
            window = window_class(settings=self.settings)
        else:
            window = window_class()
        self.opened_windows.append(window)
        window.show()
        return window

    def open_license_settings_window(self):
        window_class = self.destination_window_classes["license_settings"]
        window = window_class(
            settings_service=self.settings_service,
            initial_settings=self.settings,
            on_saved=self.apply_settings,
        )
        self.opened_windows.append(window)
        window.show()
        return window

    def _license_status_text(self, settings: dict) -> str:
        try:
            validate_license_device_settings(
                settings.get("license_id", ""),
                settings.get("device_role", ""),
            )
        except (AttributeError, LicenseSettingsValidationError):
            if settings.get("license_id") or settings.get("device_role"):
                return "不正"
            return "未設定"
        return "設定済"
