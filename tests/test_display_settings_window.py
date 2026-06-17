import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication

from app.windows.display_settings_window import DisplaySettingsWindow
from config.settings import DEFAULT_APP_SETTINGS


@pytest.fixture(scope="session")
def qt_application():
    application = QApplication.instance() or QApplication([])
    return application


class StubSettingsService:
    def __init__(self, settings=None, save_error=None):
        self.settings = settings or DEFAULT_APP_SETTINGS.copy()
        self.save_error = save_error
        self.saved_settings = None

    def load(self):
        return {
            **self.settings,
            "display_settings": dict(self.settings["display_settings"]),
        }

    def save(self, settings):
        if self.save_error is not None:
            raise self.save_error
        self.saved_settings = {
            **settings,
            "display_settings": dict(settings["display_settings"]),
        }


def test_display_settings_window_closes_when_close_button_is_clicked(qt_application):
    window = DisplaySettingsWindow(settings_service=StubSettingsService())
    window.show()

    window.closeButton.click()

    assert not window.isVisible()


def test_display_settings_window_saves_display_settings(qt_application):
    service = StubSettingsService()
    messages = []
    window = DisplaySettingsWindow(settings_service=service)
    window._show_info = lambda title, message: messages.append((title, message))

    window.displayModeComboBox.setCurrentIndex(
        window.displayModeComboBox.findText("透過")
    )
    window.backgroundColorLineEdit.setText("#112233")
    window.textColorLineEdit.setText("#445566")
    window.fontSizeSpinBox.setValue(48)
    window.opacitySpinBox.setValue(75)
    window.alwaysOnTopCheckBox.setChecked(False)
    window.saveButton.click()

    assert service.saved_settings["display_settings"] == {
        "always_on_top": False,
        "transparent_mode": True,
        "font_size": 48,
        "text_color": "#445566",
        "background_color": "#112233",
        "opacity": 0.75,
    }
    assert messages == [("表示設定", "保存しました。")]
    window.close()


def test_display_settings_window_reset_defaults_updates_form(qt_application):
    window = DisplaySettingsWindow(settings_service=StubSettingsService())
    window.backgroundColorLineEdit.setText("#112233")
    window.textColorLineEdit.setText("#445566")
    window.fontSizeSpinBox.setValue(48)
    window.opacitySpinBox.setValue(75)
    window.alwaysOnTopCheckBox.setChecked(False)

    window.resetDefaultsButton.click()

    defaults = DEFAULT_APP_SETTINGS["display_settings"]
    assert window.backgroundColorLineEdit.text() == defaults["background_color"]
    assert window.textColorLineEdit.text() == defaults["text_color"]
    assert window.fontSizeSpinBox.value() == defaults["font_size"]
    assert window.opacitySpinBox.value() == round(defaults["opacity"] * 100)
    assert window.alwaysOnTopCheckBox.isChecked() == defaults["always_on_top"]
    window.close()


def test_display_settings_window_preview_applies_style(qt_application):
    window = DisplaySettingsWindow(settings_service=StubSettingsService())
    window.backgroundColorLineEdit.setText("#112233")
    window.textColorLineEdit.setText("#445566")
    window.fontSizeSpinBox.setValue(48)
    window.opacitySpinBox.setValue(75)

    window.previewButton.click()

    style_sheet = window.centralWidget().styleSheet()
    assert "background-color: #112233" in style_sheet
    assert "color: #445566" in style_sheet
    assert "font-size: 48px" in style_sheet
    assert window.windowOpacity() == pytest.approx(0.75, abs=0.01)
    window.close()


def test_display_settings_window_shows_error_for_invalid_color(qt_application):
    service = StubSettingsService()
    errors = []
    window = DisplaySettingsWindow(settings_service=service)
    window._show_error = lambda title, message: errors.append((title, message))
    window.backgroundColorLineEdit.setText("invalid-color")

    window.saveButton.click()

    assert errors == [("表示設定", "背景色は有効な色コードを入力してください。")]
    assert service.saved_settings is None
    window.close()
