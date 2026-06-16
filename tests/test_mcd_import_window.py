import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication

from app.models.common import CALCULATION_MODE_DIRECT, CALCULATION_MODE_SIMPLE
from app.models.meeting import MeetingStartSettings
from app.services.mcd_service import export_mcd
from app.windows.mcd_import_window import McdImportWindow
from app.windows.meeting_start_settings_window import MeetingStartSettingsWindow


@pytest.fixture(scope="session")
def qt_application():
    application = QApplication.instance() or QApplication([])
    return application


def test_mcd_import_window_chooses_mcd_file(qt_application, monkeypatch):
    window = McdImportWindow(settings={"device_role": "viewer", "license_id": "LIC-1"})
    monkeypatch.setattr(
        "app.windows.mcd_import_window.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: ("meeting.mcd", "MCD Files (*.mcd)"),
    )

    window.choose_mcd_file()

    assert window.mcdFileLineEdit.text() == "meeting.mcd"
    window.close()


def test_mcd_import_window_loads_mcd_with_current_license_settings(qt_application):
    loaded_calls = []
    loaded_settings = MeetingStartSettings(
        meeting_name="Sales Meeting",
        calculation_mode=CALCULATION_MODE_DIRECT,
        total_hourly_rate=12000,
    )

    def mcd_loader(input_path, current_device_role, current_license_id):
        loaded_calls.append((input_path, current_device_role, current_license_id))
        return loaded_settings

    applied_settings = []
    window = McdImportWindow(
        settings={"device_role": "viewer", "license_id": "lic-1"},
        on_load=applied_settings.append,
        mcd_loader=mcd_loader,
    )
    window.mcdFileLineEdit.setText("meeting.mcd")

    result = window.load_display_data()

    assert result == loaded_settings
    assert loaded_calls[0][0].name == "meeting.mcd"
    assert loaded_calls[0][1] == "viewer"
    assert loaded_calls[0][2] == "lic-1"
    assert applied_settings == [loaded_settings]
    window.close()


def test_mcd_import_window_shows_error_when_load_fails(qt_application):
    errors = []

    def mcd_loader(input_path, current_device_role, current_license_id):
        raise ValueError("invalid mcd")

    window = McdImportWindow(
        settings={"device_role": "viewer", "license_id": "lic-1"},
        on_load=lambda meeting_settings: None,
        mcd_loader=mcd_loader,
    )
    window._show_error = lambda title, message: errors.append((title, message))
    window.mcdFileLineEdit.setText("meeting.mcd")

    result = window.load_display_data()

    assert result is None
    assert errors
    window.close()


def test_mcd_import_window_uses_mcd_service_read_restriction(
    qt_application,
    tmp_path,
):
    errors = []
    mcd_path = tmp_path / "meeting.mcd"
    export_mcd(
        MeetingStartSettings(
            meeting_name="Sales Meeting",
            calculation_mode=CALCULATION_MODE_SIMPLE,
            total_hourly_rate=12000,
        ),
        mcd_path,
        created_device_role="master",
        license_id="LIC-1",
    )

    window = McdImportWindow(settings={"device_role": "master", "license_id": "LIC-1"})
    window._show_error = lambda title, message: errors.append((title, message))
    window.mcdFileLineEdit.setText(str(mcd_path))

    result = window.load_display_data()

    assert result is None
    assert errors
    window.close()


def test_mcd_import_window_reflects_loaded_settings_to_meeting_start_settings_window(
    qt_application,
    tmp_path,
):
    mcd_path = tmp_path / "meeting.mcd"
    export_mcd(
        MeetingStartSettings(
            meeting_name="Sales Meeting",
            calculation_mode=CALCULATION_MODE_DIRECT,
            total_hourly_rate=15000,
        ),
        mcd_path,
        created_device_role="master",
        license_id="MASTER-1",
    )
    parent_window = MeetingStartSettingsWindow(
        settings={"device_role": "viewer", "license_id": "VIEWER-1"}
    )

    mcd_window = parent_window.open_destination_window("display_data")
    mcd_window.mcdFileLineEdit.setText(str(mcd_path))

    result = mcd_window.load_display_data()

    assert result == MeetingStartSettings(
        meeting_name="Sales Meeting",
        calculation_mode=CALCULATION_MODE_DIRECT,
        total_hourly_rate=15000,
    )
    assert parent_window.meetingNameLineEdit.text() == "Sales Meeting"
    assert parent_window.totalHourlyRateSpinBox.value() == 15000
    assert parent_window.calculationModeComboBox.currentData() == CALCULATION_MODE_DIRECT
    mcd_window.close()
    parent_window.close()
