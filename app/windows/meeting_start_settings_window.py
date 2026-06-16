from __future__ import annotations

from inspect import signature

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox

from app.models.common import (
    CALCULATION_MODE_DIRECT,
    CALCULATION_MODE_DISPLAY_DATA,
    CALCULATION_MODE_PRECISE,
    CALCULATION_MODE_SIMPLE,
)
from app.models.meeting import MeetingStartSettings
from app.services.license_settings_service import DEVICE_ROLE_VIEWER
from app.services.settings_service import SettingsService
from app.windows.base_window import UiWindow
from app.windows.count_display_window import CountDisplayWindow
from app.windows.direct_input_window import DirectInputWindow
from app.windows.mcd_import_window import McdImportWindow
from app.windows.precise_participant_selection_window import (
    PreciseParticipantSelectionWindow,
)
from app.windows.simple_role_count_window import SimpleRoleCountWindow


CALCULATION_MODE_LABELS = {
    CALCULATION_MODE_PRECISE: "精密",
    CALCULATION_MODE_SIMPLE: "簡易",
    CALCULATION_MODE_DISPLAY_DATA: "表示用データ読込",
    CALCULATION_MODE_DIRECT: "直接入力",
}


class MeetingStartSettingsWindow(UiWindow):
    ui_file_name = "meeting_start_settings.ui"

    def __init__(
        self,
        settings: dict | None = None,
        settings_service: SettingsService | None = None,
        destination_window_classes: dict[str, type] | None = None,
    ) -> None:
        super().__init__()
        self.settings = settings or {}
        self.settings_service = settings_service
        self.destination_window_classes = destination_window_classes or {
            CALCULATION_MODE_PRECISE: PreciseParticipantSelectionWindow,
            CALCULATION_MODE_SIMPLE: SimpleRoleCountWindow,
            CALCULATION_MODE_DISPLAY_DATA: McdImportWindow,
            CALCULATION_MODE_DIRECT: DirectInputWindow,
            "count_display": CountDisplayWindow,
        }
        self.opened_windows = []
        self.current_settings: MeetingStartSettings | None = None

        self._configure_calculation_mode_combo_box()
        self.calculationModeComboBox.activated.connect(
            self.open_selected_calculation_mode_window
        )
        self.startButton.clicked.connect(self.start_meeting)
        self.closeButton.clicked.connect(self.close)

    def collect_settings(self) -> MeetingStartSettings:
        return MeetingStartSettings(
            meeting_name=self.meetingNameLineEdit.text(),
            calculation_mode=self._selected_calculation_mode(),
            total_hourly_rate=self.totalHourlyRateSpinBox.value(),
        )

    def start_meeting(self):
        try:
            meeting_settings = self.collect_settings()
        except Exception:
            self._show_error("会議開始設定", "合算時間単価は1円以上で入力してください。")
            return None

        self.current_settings = meeting_settings
        return self.open_count_display_window()

    def open_selected_calculation_mode_window(self):
        calculation_mode = self._selected_calculation_mode()
        if calculation_mode == CALCULATION_MODE_PRECISE and self._is_viewer():
            self._show_error("会議開始設定", "子機では精密モードを使用できません。")
            return None
        return self.open_destination_window(calculation_mode)

    def open_count_display_window(self):
        return self.open_destination_window("count_display")

    def open_destination_window(self, destination: str):
        window_class = self.destination_window_classes[destination]
        if destination == CALCULATION_MODE_PRECISE and self._accepts_on_confirm(
            window_class
        ):
            window = window_class(
                settings=self.settings,
                on_confirm=self.apply_precise_input,
            )
        elif destination == CALCULATION_MODE_DIRECT and self._accepts_on_confirm(
            window_class
        ):
            window = window_class(on_confirm=self.apply_direct_input)
        elif destination == CALCULATION_MODE_SIMPLE and self._accepts_on_confirm(
            window_class
        ):
            window = window_class(
                settings=self.settings,
                on_confirm=self.apply_simple_input,
            )
        elif destination == CALCULATION_MODE_DISPLAY_DATA and self._accepts_on_load(
            window_class
        ):
            window = window_class(
                settings=self.settings,
                on_load=self.apply_display_data,
            )
        elif destination == "count_display" and self._accepts_meeting_settings(
            window_class
        ):
            if self._accepts_settings(window_class):
                kwargs = {
                    "meeting_settings": self.current_settings,
                    "settings": self.settings,
                }
                if self._accepts_settings_service(window_class):
                    kwargs["settings_service"] = self.settings_service
                window = window_class(**kwargs)
            else:
                window = window_class(meeting_settings=self.current_settings)
        else:
            window = window_class()
        self.opened_windows.append(window)
        window.show()
        return window

    def apply_precise_input(self, total_hourly_rate: int) -> None:
        self.totalHourlyRateSpinBox.setValue(total_hourly_rate)
        self.calculationModeComboBox.setCurrentIndex(
            self.calculationModeComboBox.findData(CALCULATION_MODE_PRECISE)
        )

    def apply_direct_input(self, total_hourly_rate: int) -> None:
        self.totalHourlyRateSpinBox.setValue(total_hourly_rate)
        self.calculationModeComboBox.setCurrentIndex(
            self.calculationModeComboBox.findData(CALCULATION_MODE_DIRECT)
        )

    def apply_simple_input(self, total_hourly_rate: int) -> None:
        self.totalHourlyRateSpinBox.setValue(total_hourly_rate)
        self.calculationModeComboBox.setCurrentIndex(
            self.calculationModeComboBox.findData(CALCULATION_MODE_SIMPLE)
        )

    def apply_display_data(self, meeting_settings: MeetingStartSettings) -> None:
        self.meetingNameLineEdit.setText(meeting_settings.meeting_name)
        self.totalHourlyRateSpinBox.setValue(meeting_settings.total_hourly_rate)
        self.calculationModeComboBox.setCurrentIndex(
            self.calculationModeComboBox.findData(meeting_settings.calculation_mode)
        )

    def _configure_calculation_mode_combo_box(self) -> None:
        self.calculationModeComboBox.clear()
        for calculation_mode, label in CALCULATION_MODE_LABELS.items():
            self.calculationModeComboBox.addItem(label, calculation_mode)

        if self._is_viewer():
            precise_index = self.calculationModeComboBox.findData(
                CALCULATION_MODE_PRECISE
            )
            item = self.calculationModeComboBox.model().item(precise_index)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.calculationModeComboBox.setCurrentIndex(
                self.calculationModeComboBox.findData(CALCULATION_MODE_SIMPLE)
            )

    def _selected_calculation_mode(self) -> str:
        calculation_mode = self.calculationModeComboBox.currentData()
        return calculation_mode if isinstance(calculation_mode, str) else ""

    def _is_viewer(self) -> bool:
        return self.settings.get("device_role") == DEVICE_ROLE_VIEWER

    def _accepts_on_confirm(self, window_class: type) -> bool:
        return "on_confirm" in signature(window_class).parameters

    def _accepts_on_load(self, window_class: type) -> bool:
        return "on_load" in signature(window_class).parameters

    def _accepts_meeting_settings(self, window_class: type) -> bool:
        return "meeting_settings" in signature(window_class).parameters

    def _accepts_settings(self, window_class: type) -> bool:
        return "settings" in signature(window_class).parameters

    def _accepts_settings_service(self, window_class: type) -> bool:
        return "settings_service" in signature(window_class).parameters

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)
