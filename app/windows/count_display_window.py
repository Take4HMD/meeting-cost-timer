from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMessageBox

from app.models.common import CALCULATION_MODE_DIRECT
from app.models.meeting import MeetingResult, MeetingStartSettings
from app.services.calculation_service import (
    calculate_actual_count_seconds,
    calculate_meeting_cost,
    round_meeting_cost_for_output,
)
from app.services.settings_service import SettingsService
from app.windows.base_window import UiWindow
from app.windows.result_export_window import ResultExportWindow


class CountDisplayWindow(UiWindow):
    ui_file_name = "count_display.ui"

    def __init__(
        self,
        meeting_settings: MeetingStartSettings | None = None,
        settings: dict | None = None,
        settings_service: SettingsService | None = None,
        now_provider: Callable[[], datetime] | None = None,
        result_export_window_class: type = ResultExportWindow,
    ) -> None:
        super().__init__()
        self.meeting_settings = meeting_settings or MeetingStartSettings(
            meeting_name="",
            calculation_mode=CALCULATION_MODE_DIRECT,
            total_hourly_rate=1,
        )
        self.settings = settings or {}
        self.settings_service = settings_service
        self.now_provider = now_provider or datetime.now
        self.result_export_window_class = result_export_window_class
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_count)

        self.start_datetime: datetime | None = None
        self.pause_started_at: datetime | None = None
        self.pause_periods: list[tuple[datetime, datetime]] = []
        self.actual_count_seconds = 0
        self.meeting_cost = 0.0
        self.last_result: MeetingResult | None = None
        self.opened_windows = []

        self.startButton.clicked.connect(self.start_count)
        self.pauseButton.clicked.connect(self.pause_count)
        self.resumeButton.clicked.connect(self.resume_count)
        self.finishButton.clicked.connect(self.finish_count)
        self._update_cost_label()

    def start_count(self) -> None:
        self.start_datetime = self.now_provider()
        self.pause_started_at = None
        self.pause_periods = []
        self.actual_count_seconds = 0
        self.meeting_cost = 0.0
        self.last_result = None
        self._update_cost_label()
        self.timer.start()

    def update_count(self) -> None:
        if self.start_datetime is None or self.pause_started_at is not None:
            return

        self.actual_count_seconds = calculate_actual_count_seconds(
            self.start_datetime,
            self.now_provider(),
            self.pause_periods,
        )
        self.meeting_cost = calculate_meeting_cost(
            self.meeting_settings.total_hourly_rate,
            self.actual_count_seconds,
        )
        self._update_cost_label()

    def pause_count(self) -> None:
        if self.start_datetime is None or self.pause_started_at is not None:
            return

        self.pause_started_at = self.now_provider()
        self.timer.stop()

    def resume_count(self) -> None:
        if self.start_datetime is None or self.pause_started_at is None:
            return

        resumed_at = self.now_provider()
        self.pause_periods.append((self.pause_started_at, resumed_at))
        self.pause_started_at = None
        self.timer.start()
        self.update_count()

    def finish_count(self) -> MeetingResult:
        if self.start_datetime is None:
            self.start_count()

        end_datetime = self.now_provider()
        pause_periods = list(self.pause_periods)
        if self.pause_started_at is not None:
            pause_periods.append((self.pause_started_at, end_datetime))
            self.pause_started_at = None

        self.timer.stop()
        self.actual_count_seconds = calculate_actual_count_seconds(
            self.start_datetime,
            end_datetime,
            pause_periods,
        )
        self.meeting_cost = calculate_meeting_cost(
            self.meeting_settings.total_hourly_rate,
            self.actual_count_seconds,
        )
        self._update_cost_label()
        self.last_result = MeetingResult(
            meeting_name=self.meeting_settings.meeting_name,
            calculation_mode=self.meeting_settings.calculation_mode,
            start_datetime=self.start_datetime,
            end_datetime=end_datetime,
            actual_count_seconds=self.actual_count_seconds,
            total_hourly_rate=self.meeting_settings.total_hourly_rate,
            meeting_cost=self.meeting_cost,
        )
        if self._confirm_result_export():
            self.open_result_export_window(self.last_result)
        return self.last_result

    def open_result_export_window(self, meeting_result: MeetingResult):
        window = self.result_export_window_class(
            meeting_result=meeting_result,
            settings=self.settings,
            settings_service=self.settings_service,
        )
        self.opened_windows.append(window)
        window.show()
        return window

    def _update_cost_label(self) -> None:
        rounded_cost = round_meeting_cost_for_output(self.meeting_cost)
        self.costLabel.setText(f"{rounded_cost}円")

    def _confirm_result_export(self) -> bool:
        reply = QMessageBox.question(
            self,
            "結果出力",
            "会議結果をCSV出力しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        return reply == QMessageBox.StandardButton.Yes
