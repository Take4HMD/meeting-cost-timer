from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem

from app.models.participant import Participant
from app.services.calculation_service import calculate_precise_total_hourly_rate
from app.services.license_settings_service import DEVICE_ROLE_VIEWER
from app.services.participant_master_service import ParticipantMasterService
from app.windows.base_window import UiWindow


class PreciseParticipantSelectionWindow(UiWindow):
    ui_file_name = "precise_participant_selection.ui"

    def __init__(
        self,
        settings: dict | None = None,
        participant_master_service: ParticipantMasterService | None = None,
        on_confirm: Callable[[int], None] | None = None,
        calculator=calculate_precise_total_hourly_rate,
    ) -> None:
        super().__init__()
        self.settings = settings or {}
        self.participant_master_service = (
            participant_master_service or ParticipantMasterService()
        )
        self.on_confirm = on_confirm
        self.calculator = calculator
        self.participants: list[Participant] = []

        self.confirmButton.clicked.connect(self.confirm_selection)
        self.clearButton.clicked.connect(self.clear_selection)
        self.closeButton.clicked.connect(self.close)
        self.apply_device_role()
        self.load_participants()

    def apply_device_role(self) -> None:
        if self.settings.get("device_role") != DEVICE_ROLE_VIEWER:
            return

        self.searchLineEdit.setEnabled(False)
        self.departmentFilterComboBox.setEnabled(False)
        self.positionFilterComboBox.setEnabled(False)
        self.participantSelectionTable.setEnabled(False)
        self.confirmButton.setEnabled(False)
        self.clearButton.setEnabled(False)

    def load_participants(self) -> None:
        if self._is_viewer():
            self.set_participants([])
            return

        license_id = self.settings.get("license_id", "")
        if not license_id:
            self.set_participants([])
            return

        try:
            loaded_participants = self.participant_master_service.load_participants(
                license_id
            )
        except Exception:
            self._show_error(
                "精密モード",
                "参加者マスタの読込に失敗しました。",
            )
            self.set_participants([])
            return

        self.set_participants(
            [participant for participant in loaded_participants if participant.is_active]
        )

    def set_participants(self, participants: list[Participant]) -> None:
        self.participants = participants
        self.participantSelectionTable.setRowCount(0)
        for participant in participants:
            self._append_participant_row(participant)

    def confirm_selection(self) -> int | None:
        if self._is_viewer():
            self._show_error(
                "精密モード",
                "子機では精密モードを使用できません。",
            )
            return None

        try:
            total_hourly_rate = self.calculator(self.collect_selected_participants())
        except Exception:
            self._show_error(
                "精密モード",
                "参加者を1名以上選択してください。",
            )
            return None

        if self.on_confirm is not None:
            self.on_confirm(total_hourly_rate)
        self.close()
        return total_hourly_rate

    def collect_selected_participants(self) -> list[Participant]:
        selected_participants = []
        for row in range(self.participantSelectionTable.rowCount()):
            item = self.participantSelectionTable.item(row, 0)
            if item is not None and item.checkState() == Qt.CheckState.Checked:
                selected_participants.append(self._row_participant(row))
        return selected_participants

    def clear_selection(self) -> None:
        for row in range(self.participantSelectionTable.rowCount()):
            item = self.participantSelectionTable.item(row, 0)
            if item is not None:
                item.setCheckState(Qt.CheckState.Unchecked)

    def _append_participant_row(self, participant: Participant) -> None:
        row = self.participantSelectionTable.rowCount()
        self.participantSelectionTable.insertRow(row)

        selection_item = QTableWidgetItem("")
        selection_item.setFlags(
            selection_item.flags()
            | Qt.ItemFlag.ItemIsUserCheckable
            | Qt.ItemFlag.ItemIsEnabled
        )
        selection_item.setCheckState(Qt.CheckState.Unchecked)
        selection_item.setData(Qt.ItemDataRole.UserRole, participant)
        self.participantSelectionTable.setItem(row, 0, selection_item)
        self._set_item(row, 1, participant.name)
        self._set_item(row, 2, participant.department)
        self._set_item(row, 3, participant.position)
        self._set_item(row, 4, participant.display_name)

    def _row_participant(self, row: int) -> Participant:
        item = self.participantSelectionTable.item(row, 0)
        if item is None:
            raise ValueError("participant is required")
        participant = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(participant, Participant):
            raise ValueError("participant is invalid")
        return participant

    def _set_item(self, row: int, column: int, text: str) -> None:
        self.participantSelectionTable.setItem(row, column, QTableWidgetItem(text))

    def _is_viewer(self) -> bool:
        return self.settings.get("device_role") == DEVICE_ROLE_VIEWER

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)
