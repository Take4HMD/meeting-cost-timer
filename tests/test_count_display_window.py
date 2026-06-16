import os
from datetime import datetime, timedelta

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication

from app.models.common import CALCULATION_MODE_DIRECT, CALCULATION_MODE_SIMPLE
from app.models.meeting import MeetingResult, MeetingStartSettings
from app.windows.count_display_window import CountDisplayWindow
from app.windows.meeting_start_settings_window import MeetingStartSettingsWindow


@pytest.fixture(scope="session")
def qt_application():
    application = QApplication.instance() or QApplication([])
    return application


class FakeClock:
    def __init__(self, current_datetime):
        self.current_datetime = current_datetime

    def now(self):
        return self.current_datetime

    def advance(self, seconds):
        self.current_datetime += timedelta(seconds=seconds)


class CountDisplayDestinationWindow:
    created = []

    def __init__(self, meeting_settings=None, settings=None, settings_service=None):
        self.meeting_settings = meeting_settings
        self.settings = settings
        self.settings_service = settings_service
        self.was_shown = False
        self.__class__.created.append(self)

    def show(self):
        self.was_shown = True


class ResultExportDestinationWindow:
    created = []

    def __init__(self, meeting_result=None, settings=None, settings_service=None):
        self.meeting_result = meeting_result
        self.settings = settings
        self.settings_service = settings_service
        self.was_shown = False
        self.__class__.created.append(self)

    def show(self):
        self.was_shown = True


def _meeting_settings(total_hourly_rate=3600):
    return MeetingStartSettings(
        meeting_name="Sales Meeting",
        calculation_mode=CALCULATION_MODE_SIMPLE,
        total_hourly_rate=total_hourly_rate,
    )


def test_count_display_window_receives_meeting_settings(qt_application):
    settings = _meeting_settings(total_hourly_rate=7200)

    window = CountDisplayWindow(meeting_settings=settings)

    assert window.meeting_settings == settings
    assert window.actual_count_seconds == 0
    assert window.costLabel.text() == "0円"
    window.close()


def test_count_display_window_updates_count_and_rounded_cost(qt_application):
    clock = FakeClock(datetime(2026, 6, 4, 10, 0, 0))
    window = CountDisplayWindow(
        meeting_settings=_meeting_settings(total_hourly_rate=3600),
        now_provider=clock.now,
    )

    window.start_count()
    clock.advance(5)
    window.update_count()

    assert window.actual_count_seconds == 5
    assert window.meeting_cost == 5
    assert window.costLabel.text() == "5円"
    assert window.timer.isActive()
    window.close()


def test_count_display_window_rounds_meeting_cost_for_display(qt_application):
    clock = FakeClock(datetime(2026, 6, 4, 10, 0, 0))
    window = CountDisplayWindow(
        meeting_settings=_meeting_settings(total_hourly_rate=1000),
        now_provider=clock.now,
    )

    window.start_count()
    clock.advance(2)
    window.update_count()

    assert window.meeting_cost == pytest.approx(1000 / 3600 * 2)
    assert window.costLabel.text() == "1円"
    window.close()


def test_count_display_window_pause_and_resume_exclude_pause_seconds(qt_application):
    clock = FakeClock(datetime(2026, 6, 4, 10, 0, 0))
    window = CountDisplayWindow(
        meeting_settings=_meeting_settings(total_hourly_rate=3600),
        now_provider=clock.now,
    )

    window.start_count()
    clock.advance(5)
    window.update_count()
    window.pause_count()
    clock.advance(10)
    window.update_count()

    assert window.actual_count_seconds == 5
    assert not window.timer.isActive()

    window.resume_count()
    clock.advance(5)
    window.update_count()

    assert window.actual_count_seconds == 10
    assert window.costLabel.text() == "10円"
    assert window.timer.isActive()
    window.close()


def test_count_display_window_finish_creates_meeting_result(qt_application):
    ResultExportDestinationWindow.created = []
    clock = FakeClock(datetime(2026, 6, 4, 10, 0, 0))
    settings = _meeting_settings(total_hourly_rate=3600)
    app_settings = {"output_settings": {"last_output_dir": "", "default_format": "csv"}}
    settings_service = object()
    window = CountDisplayWindow(
        meeting_settings=settings,
        settings=app_settings,
        settings_service=settings_service,
        now_provider=clock.now,
        result_export_window_class=ResultExportDestinationWindow,
    )
    window._confirm_result_export = lambda: True

    window.start_count()
    clock.advance(5)
    window.pause_count()
    clock.advance(10)
    window.resume_count()
    clock.advance(5)

    result = window.finish_count()

    assert result == MeetingResult(
        meeting_name="Sales Meeting",
        calculation_mode=CALCULATION_MODE_SIMPLE,
        start_datetime=datetime(2026, 6, 4, 10, 0, 0),
        end_datetime=datetime(2026, 6, 4, 10, 0, 20),
        actual_count_seconds=10,
        total_hourly_rate=3600,
        meeting_cost=10,
    )
    assert window.last_result == result
    assert not window.timer.isActive()
    assert window.costLabel.text() == "10円"
    assert ResultExportDestinationWindow.created[0].meeting_result == result
    assert ResultExportDestinationWindow.created[0].settings == app_settings
    assert ResultExportDestinationWindow.created[0].settings_service == settings_service
    assert ResultExportDestinationWindow.created[0].was_shown
    window.close()


def test_count_display_window_finish_keeps_last_result_without_export_on_no(
    qt_application,
):
    ResultExportDestinationWindow.created = []
    clock = FakeClock(datetime(2026, 6, 4, 10, 0, 0))
    window = CountDisplayWindow(
        meeting_settings=_meeting_settings(total_hourly_rate=3600),
        now_provider=clock.now,
        result_export_window_class=ResultExportDestinationWindow,
    )
    window._confirm_result_export = lambda: False

    window.start_count()
    clock.advance(5)

    result = window.finish_count()

    assert window.last_result == result
    assert result.actual_count_seconds == 5
    assert ResultExportDestinationWindow.created == []
    window.close()


def test_meeting_start_settings_window_passes_settings_to_count_display_window(
    qt_application,
):
    CountDisplayDestinationWindow.created = []
    settings_service = object()
    window = MeetingStartSettingsWindow(
        settings={"device_role": "master"},
        settings_service=settings_service,
        destination_window_classes={
            "precise": CountDisplayDestinationWindow,
            "simple": CountDisplayDestinationWindow,
            "display_data": CountDisplayDestinationWindow,
            "direct": CountDisplayDestinationWindow,
            "count_display": CountDisplayDestinationWindow,
        },
    )
    window.meetingNameLineEdit.setText("Sales Meeting")
    window.calculationModeComboBox.setCurrentIndex(
        window.calculationModeComboBox.findData(CALCULATION_MODE_DIRECT)
    )
    window.totalHourlyRateSpinBox.setValue(12000)

    opened_window = window.start_meeting()

    assert opened_window is CountDisplayDestinationWindow.created[0]
    assert opened_window.was_shown
    assert opened_window.meeting_settings == MeetingStartSettings(
        meeting_name="Sales Meeting",
        calculation_mode=CALCULATION_MODE_DIRECT,
        total_hourly_rate=12000,
    )
    assert opened_window.settings == {"device_role": "master"}
    assert opened_window.settings_service == settings_service
    window.close()
