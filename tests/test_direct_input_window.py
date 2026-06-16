import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication

from app.models.common import CALCULATION_MODE_DIRECT
from app.windows.direct_input_window import DirectInputWindow
from app.windows.meeting_start_settings_window import MeetingStartSettingsWindow


@pytest.fixture(scope="session")
def qt_application():
    application = QApplication.instance() or QApplication([])
    return application


def test_direct_input_window_confirms_valid_integer(qt_application):
    confirmed_values = []
    window = DirectInputWindow(on_confirm=confirmed_values.append)
    window.totalHourlyRateLineEdit.setText("12000")

    result = window.confirm_input()

    assert result == 12000
    assert confirmed_values == [12000]
    window.close()


def test_direct_input_window_allows_comma_separated_integer(qt_application):
    confirmed_values = []
    window = DirectInputWindow(on_confirm=confirmed_values.append)
    window.totalHourlyRateLineEdit.setText("12,000")

    result = window.confirm_input()

    assert result == 12000
    assert confirmed_values == [12000]
    window.close()


@pytest.mark.parametrize("value", ["", "0", "-1", "100.5", "abc"])
def test_direct_input_window_shows_error_for_invalid_value(qt_application, value):
    confirmed_values = []
    errors = []
    window = DirectInputWindow(on_confirm=confirmed_values.append)
    window._show_error = lambda title, message: errors.append((title, message))
    window.totalHourlyRateLineEdit.setText(value)

    result = window.confirm_input()

    assert result is None
    assert confirmed_values == []
    assert errors
    window.close()


def test_direct_input_window_reflects_value_to_meeting_start_settings_window(
    qt_application,
):
    parent_window = MeetingStartSettingsWindow(settings={"device_role": "master"})
    parent_window.calculationModeComboBox.setCurrentIndex(
        parent_window.calculationModeComboBox.findData("precise")
    )

    direct_window = parent_window.open_destination_window(CALCULATION_MODE_DIRECT)
    direct_window.totalHourlyRateLineEdit.setText("15,000")

    result = direct_window.confirm_input()

    assert result == 15000
    assert parent_window.totalHourlyRateSpinBox.value() == 15000
    assert parent_window.calculationModeComboBox.currentData() == CALCULATION_MODE_DIRECT
    direct_window.close()
    parent_window.close()
