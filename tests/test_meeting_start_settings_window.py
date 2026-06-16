import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from app.models.common import (
    CALCULATION_MODE_DIRECT,
    CALCULATION_MODE_DISPLAY_DATA,
    CALCULATION_MODE_PRECISE,
    CALCULATION_MODE_SIMPLE,
)
from app.models.meeting import MeetingStartSettings
from app.windows.meeting_start_settings_window import MeetingStartSettingsWindow


@pytest.fixture(scope="session")
def qt_application():
    application = QApplication.instance() or QApplication([])
    return application


class DestinationWindow:
    created = []

    def __init__(self):
        self.was_shown = False
        self.__class__.created.append(self)

    def show(self):
        self.was_shown = True


def _destination_classes():
    return {
        CALCULATION_MODE_PRECISE: DestinationWindow,
        CALCULATION_MODE_SIMPLE: DestinationWindow,
        CALCULATION_MODE_DISPLAY_DATA: DestinationWindow,
        CALCULATION_MODE_DIRECT: DestinationWindow,
        "count_display": DestinationWindow,
    }


def _mode_texts(window):
    return [
        window.calculationModeComboBox.itemText(index)
        for index in range(window.calculationModeComboBox.count())
    ]


def test_meeting_start_settings_window_shows_specified_calculation_modes_for_master(
    qt_application,
):
    window = MeetingStartSettingsWindow(
        settings={"device_role": "master"},
        destination_window_classes=_destination_classes(),
    )

    assert _mode_texts(window) == ["精密", "簡易", "表示用データ読込", "直接入力"]
    assert window.calculationModeComboBox.currentData() == CALCULATION_MODE_PRECISE
    window.close()


def test_meeting_start_settings_window_disables_precise_mode_for_viewer(
    qt_application,
):
    window = MeetingStartSettingsWindow(
        settings={"device_role": "viewer"},
        destination_window_classes=_destination_classes(),
    )

    precise_index = window.calculationModeComboBox.findData(CALCULATION_MODE_PRECISE)
    precise_item = window.calculationModeComboBox.model().item(precise_index)

    assert _mode_texts(window) == ["精密", "簡易", "表示用データ読込", "直接入力"]
    assert not precise_item.flags() & Qt.ItemFlag.ItemIsEnabled
    assert window.calculationModeComboBox.currentData() == CALCULATION_MODE_SIMPLE
    window.close()


@pytest.mark.parametrize(
    "calculation_mode",
    [
        CALCULATION_MODE_PRECISE,
        CALCULATION_MODE_SIMPLE,
        CALCULATION_MODE_DISPLAY_DATA,
        CALCULATION_MODE_DIRECT,
    ],
)
def test_meeting_start_settings_window_opens_selected_mode_window_for_master(
    qt_application,
    calculation_mode,
):
    DestinationWindow.created = []
    window = MeetingStartSettingsWindow(
        settings={"device_role": "master"},
        destination_window_classes=_destination_classes(),
    )
    window.calculationModeComboBox.setCurrentIndex(
        window.calculationModeComboBox.findData(calculation_mode)
    )

    opened_window = window.open_selected_calculation_mode_window()

    assert opened_window is DestinationWindow.created[0]
    assert opened_window.was_shown
    assert window.opened_windows[-1] is opened_window
    window.close()


def test_meeting_start_settings_window_rejects_precise_mode_for_viewer(qt_application):
    DestinationWindow.created = []
    errors = []
    window = MeetingStartSettingsWindow(
        settings={"device_role": "viewer"},
        destination_window_classes=_destination_classes(),
    )
    window._show_error = lambda title, message: errors.append((title, message))
    window.calculationModeComboBox.setCurrentIndex(
        window.calculationModeComboBox.findData(CALCULATION_MODE_PRECISE)
    )

    opened_window = window.open_selected_calculation_mode_window()

    assert opened_window is None
    assert errors
    assert DestinationWindow.created == []
    window.close()


def test_meeting_start_settings_window_collects_settings(qt_application):
    window = MeetingStartSettingsWindow(
        settings={"device_role": "master"},
        destination_window_classes=_destination_classes(),
    )
    window.meetingNameLineEdit.setText("Sales Meeting")
    window.calculationModeComboBox.setCurrentIndex(
        window.calculationModeComboBox.findData(CALCULATION_MODE_DIRECT)
    )
    window.totalHourlyRateSpinBox.setValue(12000)

    assert window.collect_settings() == MeetingStartSettings(
        meeting_name="Sales Meeting",
        calculation_mode=CALCULATION_MODE_DIRECT,
        total_hourly_rate=12000,
    )
    window.close()


def test_meeting_start_settings_window_start_opens_count_display_when_valid(
    qt_application,
):
    DestinationWindow.created = []
    window = MeetingStartSettingsWindow(
        settings={"device_role": "master"},
        destination_window_classes=_destination_classes(),
    )
    window.meetingNameLineEdit.setText("Sales Meeting")
    window.totalHourlyRateSpinBox.setValue(12000)

    opened_window = window.start_meeting()

    assert opened_window is DestinationWindow.created[0]
    assert opened_window.was_shown
    assert window.current_settings == MeetingStartSettings(
        meeting_name="Sales Meeting",
        calculation_mode=CALCULATION_MODE_PRECISE,
        total_hourly_rate=12000,
    )
    window.close()


def test_meeting_start_settings_window_start_shows_error_when_rate_is_invalid(
    qt_application,
):
    DestinationWindow.created = []
    errors = []
    window = MeetingStartSettingsWindow(
        settings={"device_role": "master"},
        destination_window_classes=_destination_classes(),
    )
    window._show_error = lambda title, message: errors.append((title, message))
    window.totalHourlyRateSpinBox.setMinimum(0)
    window.totalHourlyRateSpinBox.setValue(0)

    opened_window = window.start_meeting()

    assert opened_window is None
    assert errors
    assert window.current_settings is None
    assert DestinationWindow.created == []
    window.close()
