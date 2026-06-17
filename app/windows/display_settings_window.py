from __future__ import annotations

from copy import deepcopy

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QMessageBox

from app.services.settings_service import SettingsService
from app.windows.base_window import UiWindow
from config.settings import DEFAULT_APP_SETTINGS


TRANSPARENT_MODE = "transparent"
BACKGROUND_MODE = "background"


class DisplaySettingsWindow(UiWindow):
    ui_file_name = "display_settings.ui"

    def __init__(
        self,
        settings_service: SettingsService | None = None,
        initial_settings: dict | None = None,
    ) -> None:
        super().__init__()
        self.settings_service = settings_service or SettingsService()
        self.settings = (
            deepcopy(initial_settings)
            if initial_settings is not None
            else self.settings_service.load()
        )

        self._configure_display_mode_combo_box()
        self.apply_display_settings(self.settings.get("display_settings", {}))
        self.previewButton.clicked.connect(self.preview_settings)
        self.saveButton.clicked.connect(self.save_settings)
        self.resetDefaultsButton.clicked.connect(self.reset_defaults)
        self.closeButton.clicked.connect(self.close)

    def apply_display_settings(self, display_settings: dict) -> None:
        transparent_mode = bool(display_settings.get("transparent_mode", False))
        mode = TRANSPARENT_MODE if transparent_mode else BACKGROUND_MODE
        index = self.displayModeComboBox.findData(mode)
        self.displayModeComboBox.setCurrentIndex(max(index, 0))
        self.backgroundColorLineEdit.setText(
            display_settings.get("background_color", "#000000")
        )
        self.textColorLineEdit.setText(display_settings.get("text_color", "#FFFFFF"))
        self.fontSizeSpinBox.setValue(int(display_settings.get("font_size", 36)))
        opacity = float(display_settings.get("opacity", 0.85))
        self.opacitySpinBox.setValue(round(opacity * 100))
        self.alwaysOnTopCheckBox.setChecked(
            bool(display_settings.get("always_on_top", True))
        )

    def preview_settings(self) -> None:
        try:
            display_settings = self._collect_display_settings()
        except ValueError as exc:
            self._show_error("表示設定", str(exc))
            return

        self._apply_preview_style(display_settings)

    def save_settings(self) -> None:
        try:
            display_settings = self._collect_display_settings()
            settings = self.settings_service.load()
            settings["display_settings"] = display_settings
            self.settings_service.save(settings)
        except ValueError as exc:
            self._show_error("表示設定", str(exc))
            return
        except Exception:
            self._show_error("表示設定", "表示設定の保存に失敗しました。")
            return

        self.settings = settings
        self._show_info("表示設定", "保存しました。")

    def reset_defaults(self) -> None:
        self.apply_display_settings(DEFAULT_APP_SETTINGS["display_settings"])

    def _configure_display_mode_combo_box(self) -> None:
        self.displayModeComboBox.clear()
        self.displayModeComboBox.addItem("透過", TRANSPARENT_MODE)
        self.displayModeComboBox.addItem("背景色あり", BACKGROUND_MODE)

    def _collect_display_settings(self) -> dict:
        background_color = self.backgroundColorLineEdit.text().strip()
        text_color = self.textColorLineEdit.text().strip()
        self._validate_color(background_color, "背景色")
        self._validate_color(text_color, "文字色")

        return {
            "always_on_top": self.alwaysOnTopCheckBox.isChecked(),
            "transparent_mode": self.displayModeComboBox.currentData()
            == TRANSPARENT_MODE,
            "font_size": self.fontSizeSpinBox.value(),
            "text_color": text_color,
            "background_color": background_color,
            "opacity": self.opacitySpinBox.value() / 100,
        }

    def _validate_color(self, color_text: str, field_name: str) -> None:
        if not color_text:
            raise ValueError(f"{field_name}を入力してください。")
        if not QColor(color_text).isValid():
            raise ValueError(f"{field_name}は有効な色コードを入力してください。")

    def _apply_preview_style(self, display_settings: dict) -> None:
        background_color = (
            "transparent"
            if display_settings["transparent_mode"]
            else display_settings["background_color"]
        )
        self.centralWidget().setStyleSheet(
            "QWidget {"
            f"background-color: {background_color};"
            f"color: {display_settings['text_color']};"
            f"font-size: {display_settings['font_size']}px;"
            "}"
        )
        self.setWindowOpacity(display_settings["opacity"])

    def _show_info(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)
