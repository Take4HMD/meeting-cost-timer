import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication

from app.services.settings_service import SettingsService
from app.startup import StartupController, has_valid_license_device_settings
from app.windows.license_settings_window import LicenseSettingsWindow
from app.windows.main_menu_window import APP_VERSION_TEXT, MainMenuWindow


@pytest.fixture(scope="session")
def qt_application():
    application = QApplication.instance() or QApplication([])
    return application


class StubSettingsService:
    def __init__(self, settings):
        self.settings = settings

    def load(self):
        return self.settings


class StubWindow:
    created_with_settings = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.was_shown = False
        self.__class__.created_with_settings.append(kwargs.get("settings"))

    def show(self):
        self.was_shown = True


class StubLicenseWindow(StubWindow):
    def __init__(self, settings_service=None, initial_settings=None, on_saved=None):
        super().__init__(
            settings_service=settings_service,
            initial_settings=initial_settings,
            on_saved=on_saved,
        )


class StubMainWindow(StubWindow):
    pass


class MenuDestinationWindow:
    created = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.was_shown = False
        self.__class__.created.append(self)

    def show(self):
        self.was_shown = True


class MenuLicenseWindow:
    created = []

    def __init__(self, settings_service=None, initial_settings=None, on_saved=None):
        self.settings_service = settings_service
        self.initial_settings = initial_settings
        self.on_saved = on_saved
        self.was_shown = False
        self.__class__.created.append(self)

    def show(self):
        self.was_shown = True


def test_has_valid_license_device_settings_detects_complete_settings():
    assert has_valid_license_device_settings(
        {"license_id": "LIC-TEST-001", "device_role": "master"}
    )


def test_has_valid_license_device_settings_rejects_missing_settings():
    assert not has_valid_license_device_settings(
        {"license_id": "", "device_role": ""}
    )


def test_startup_controller_shows_license_settings_when_settings_are_invalid():
    settings = {"license_id": "", "device_role": ""}
    controller = StartupController(
        settings_service=StubSettingsService(settings),
        main_window_class=StubMainWindow,
        license_window_class=StubLicenseWindow,
    )

    window = controller.show_initial_window()

    assert isinstance(window, StubLicenseWindow)
    assert window.was_shown
    assert window.kwargs["initial_settings"] == settings


def test_startup_controller_shows_main_menu_when_settings_are_valid():
    settings = {"license_id": "LIC-TEST-001", "device_role": "viewer"}
    settings_service = StubSettingsService(settings)
    controller = StartupController(
        settings_service=settings_service,
        main_window_class=StubMainWindow,
        license_window_class=StubLicenseWindow,
    )

    window = controller.show_initial_window()

    assert isinstance(window, StubMainWindow)
    assert window.was_shown
    assert window.kwargs["settings"] == settings
    assert window.kwargs["settings_service"] is settings_service


def test_license_settings_window_saves_valid_settings_and_calls_on_saved(
    qt_application,
    tmp_path,
):
    settings_path = tmp_path / "config" / "app_settings.json"
    service = SettingsService(settings_path, tmp_path / "logs" / "error.log")
    saved_settings = []
    window = LicenseSettingsWindow(
        settings_service=service,
        on_saved=saved_settings.append,
    )

    window.licenseIdLineEdit.setText(" lic-test-001 ")
    window.deviceRoleComboBox.setCurrentIndex(
        window.deviceRoleComboBox.findData("viewer")
    )
    window._show_error = pytest.fail

    window.save_settings()

    loaded_settings = service.load()
    assert loaded_settings["license_id"] == "LIC-TEST-001"
    assert loaded_settings["device_role"] == "viewer"
    assert saved_settings
    assert saved_settings[0]["license_id"] == "LIC-TEST-001"
    window.close()


def test_license_settings_window_shows_error_for_invalid_settings(
    qt_application,
    tmp_path,
):
    settings_path = tmp_path / "config" / "app_settings.json"
    service = SettingsService(settings_path, tmp_path / "logs" / "error.log")
    errors = []
    window = LicenseSettingsWindow(settings_service=service)
    window._show_error = lambda title, message: errors.append((title, message))

    window.licenseIdLineEdit.setText("")
    window.deviceRoleComboBox.setCurrentIndex(
        window.deviceRoleComboBox.findData("master")
    )

    window.save_settings()

    assert errors
    assert service.load()["license_id"] == ""
    assert window.licenseStatusLabel.text() == "不正"
    window.close()


def test_main_menu_window_reflects_license_settings(qt_application):
    window = MainMenuWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "master"}
    )

    assert window.deviceRoleLabel.text() == "端末種別: 親機"
    assert window.licenseStatusLabel.text() == "ライセンス状態: 設定済"
    assert window.appVersionLabel.text() == APP_VERSION_TEXT
    window.close()


def test_main_menu_window_reflects_invalid_license_settings(qt_application):
    window = MainMenuWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": ""}
    )

    assert window.deviceRoleLabel.text() == "端末種別: 未設定"
    assert window.licenseStatusLabel.text() == "ライセンス状態: 不正"
    window.close()


@pytest.mark.parametrize(
    ("button_name", "destination_key"),
    [
        ("startMeetingButton", "meeting_start"),
        ("masterMenuButton", "master_menu"),
        ("displaySettingsButton", "display_settings"),
    ],
)
def test_main_menu_buttons_open_destination_windows(
    qt_application,
    button_name,
    destination_key,
):
    MenuDestinationWindow.created = []
    settings_service = StubSettingsService(
        {"license_id": "LIC-TEST-001", "device_role": "master"}
    )
    window = MainMenuWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "master"},
        settings_service=settings_service,
        destination_window_classes={
            "meeting_start": MenuDestinationWindow,
            "master_menu": MenuDestinationWindow,
            "display_settings": MenuDestinationWindow,
            "license_settings": MenuLicenseWindow,
        },
    )

    getattr(window, button_name).click()

    assert len(MenuDestinationWindow.created) == 1
    assert MenuDestinationWindow.created[0].was_shown
    assert window.opened_windows[-1] is MenuDestinationWindow.created[0]
    assert destination_key in window.destination_window_classes
    if destination_key in {"meeting_start", "master_menu"}:
        assert MenuDestinationWindow.created[0].kwargs["settings"] == {
            "license_id": "LIC-TEST-001",
            "device_role": "master",
        }
    if destination_key == "meeting_start":
        assert (
            MenuDestinationWindow.created[0].kwargs["settings_service"]
            is settings_service
        )
    window.close()


def test_main_menu_license_button_opens_license_settings_window(qt_application):
    MenuLicenseWindow.created = []
    settings = {"license_id": "LIC-TEST-001", "device_role": "viewer"}
    settings_service = StubSettingsService(settings)
    window = MainMenuWindow(
        settings=settings,
        settings_service=settings_service,
        destination_window_classes={
            "meeting_start": MenuDestinationWindow,
            "master_menu": MenuDestinationWindow,
            "display_settings": MenuDestinationWindow,
            "license_settings": MenuLicenseWindow,
        },
    )

    window.licenseSettingsButton.click()

    opened_window = MenuLicenseWindow.created[0]
    assert opened_window.was_shown
    assert opened_window.settings_service is settings_service
    assert opened_window.initial_settings == settings
    assert opened_window.on_saved == window.apply_settings
    window.close()
