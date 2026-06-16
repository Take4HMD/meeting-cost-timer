from __future__ import annotations

from PyQt6.QtWidgets import QMessageBox

from app.services.license_settings_service import (
    DEVICE_ROLE_MASTER,
    DEVICE_ROLE_VIEWER,
    LicenseSettingsValidationError,
    validate_license_device_settings,
)
from app.services.settings_service import SettingsService
from app.windows.base_window import UiWindow


DEVICE_ROLE_LABELS = {
    DEVICE_ROLE_MASTER: "親機",
    DEVICE_ROLE_VIEWER: "子機",
}


class LicenseSettingsWindow(UiWindow):
    ui_file_name = "license_settings.ui"

    def __init__(
        self,
        settings_service: SettingsService | None = None,
        initial_settings: dict | None = None,
        on_saved=None,
    ) -> None:
        super().__init__()
        self.settings_service = settings_service or SettingsService()
        self.on_saved = on_saved
        self._configure_device_role_combo_box()
        self.saveButton.clicked.connect(self.save_settings)
        self.closeButton.clicked.connect(self.close)
        if initial_settings is not None:
            self.apply_settings(initial_settings)

    def apply_settings(self, settings: dict) -> None:
        self.licenseIdLineEdit.setText(settings.get("license_id", ""))
        device_role = settings.get("device_role", "")
        index = self.deviceRoleComboBox.findData(device_role)
        self.deviceRoleComboBox.setCurrentIndex(index)
        self._update_license_status(settings)

    def save_settings(self) -> None:
        try:
            validated_settings = validate_license_device_settings(
                self.licenseIdLineEdit.text(),
                self._selected_device_role(),
            )
            settings = self.settings_service.load()
            settings["license_id"] = validated_settings.license_id
            settings["device_role"] = validated_settings.device_role
            self.settings_service.save(settings)
        except LicenseSettingsValidationError as exc:
            self._show_error("ライセンス・端末設定", str(exc))
            self.licenseStatusLabel.setText("不正")
            return
        except Exception as exc:
            self._show_error("ライセンス・端末設定", "設定の保存に失敗しました。")
            self.licenseStatusLabel.setText("不正")
            return

        self.licenseStatusLabel.setText("設定済")
        if self.on_saved is not None:
            self.close()
            self.on_saved(settings)

    def _configure_device_role_combo_box(self) -> None:
        self.deviceRoleComboBox.clear()
        for device_role, label in DEVICE_ROLE_LABELS.items():
            self.deviceRoleComboBox.addItem(label, device_role)
        self.deviceRoleComboBox.setCurrentIndex(-1)

    def _selected_device_role(self) -> str:
        device_role = self.deviceRoleComboBox.currentData()
        return device_role if isinstance(device_role, str) else ""

    def _update_license_status(self, settings: dict) -> None:
        try:
            validate_license_device_settings(
                settings.get("license_id", ""),
                settings.get("device_role", ""),
            )
        except (AttributeError, LicenseSettingsValidationError):
            self.licenseStatusLabel.setText("未設定")
            return
        self.licenseStatusLabel.setText("設定済")

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)
