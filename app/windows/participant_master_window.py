from __future__ import annotations

import re

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem

from app.models.participant import Participant
from app.services.license_settings_service import DEVICE_ROLE_VIEWER
from app.services.participant_master_service import ParticipantMasterService
from app.windows.base_window import UiWindow


ACTIVE_TEXT = "有効"
INACTIVE_TEXT = "無効"


class ParticipantMasterWindow(UiWindow):
    ui_file_name = "participant_master.ui"

    def __init__(
        self,
        settings: dict | None = None,
        participant_master_service: ParticipantMasterService | None = None,
    ) -> None:
        super().__init__()
        self.settings = settings or {}
        self.participant_master_service = (
            participant_master_service or ParticipantMasterService()
        )
        self.participants: list[Participant] = []

        self.addRowButton.clicked.connect(self.add_empty_row)
        self.deleteRowButton.clicked.connect(self.delete_selected_rows)
        self.saveButton.clicked.connect(self.save_participants)
        self.closeButton.clicked.connect(self.close)
        self.apply_device_role()
        self.load_participants()

    def apply_device_role(self) -> None:
        if self.settings.get("device_role") != DEVICE_ROLE_VIEWER:
            return

        self.participantTable.setEnabled(False)
        self.addRowButton.setEnabled(False)
        self.deleteRowButton.setEnabled(False)
        self.saveButton.setEnabled(False)
        self.csvImportButton.setEnabled(False)

    def load_participants(self) -> None:
        if self.settings.get("device_role") == DEVICE_ROLE_VIEWER:
            self.set_participants([])
            return

        license_id = self.settings.get("license_id", "")
        if not license_id:
            self.set_participants([])
            return

        try:
            self.set_participants(
                self.participant_master_service.load_participants(license_id)
            )
        except Exception:
            self._show_error("参加者マスタ", "参加者マスタの読込に失敗しました。")
            self.set_participants([])

    def set_participants(self, participants: list[Participant]) -> None:
        self.participants = participants
        self.participantTable.setRowCount(0)
        for participant in participants:
            self._append_participant_row(participant)

    def add_empty_row(self) -> None:
        row = self.participantTable.rowCount()
        self.participantTable.insertRow(row)
        self._set_item(row, 0, ACTIVE_TEXT)
        self._set_item(row, 1, "")
        self._set_item(row, 2, "")
        self._set_item(row, 3, "")
        self._set_item(row, 4, "")
        self._set_item(row, 5, "")
        self._set_item(row, 6, "")
        self.participantTable.item(row, 0).setData(
            Qt.ItemDataRole.UserRole,
            self._next_participant_id(),
        )

    def delete_selected_rows(self) -> None:
        selected_rows = {
            index.row()
            for index in self.participantTable.selectionModel().selectedRows()
        }
        if not selected_rows:
            current_row = self.participantTable.currentRow()
            if current_row >= 0:
                selected_rows.add(current_row)

        for row in sorted(selected_rows, reverse=True):
            self.participantTable.removeRow(row)

    def save_participants(self) -> None:
        try:
            participants = self.collect_participants()
            self.participant_master_service.save_participants(
                participants,
                self.settings.get("license_id", ""),
            )
        except Exception:
            self._show_error("参加者マスタ", "参加者マスタの保存に失敗しました。")
            return

        self.participants = participants

    def collect_participants(self) -> list[Participant]:
        participants = []
        for row in range(self.participantTable.rowCount()):
            participants.append(
                Participant(
                    participant_id=self._row_participant_id(row),
                    is_active=self._is_active_cell(row),
                    name=self._cell_text(row, 1),
                    department=self._cell_text(row, 2),
                    position=self._cell_text(row, 3),
                    display_name=self._cell_text(row, 4),
                    hourly_rate=self._positive_int_cell(row, 5, "概算時間単価"),
                    sort_order=self._optional_positive_int_cell(row, 6, "表示順"),
                )
            )
        return participants

    def _append_participant_row(self, participant: Participant) -> None:
        row = self.participantTable.rowCount()
        self.participantTable.insertRow(row)
        self._set_item(row, 0, ACTIVE_TEXT if participant.is_active else INACTIVE_TEXT)
        self._set_item(row, 1, participant.name)
        self._set_item(row, 2, participant.department)
        self._set_item(row, 3, participant.position)
        self._set_item(row, 4, participant.display_name)
        self._set_item(row, 5, str(participant.hourly_rate))
        self._set_item(
            row,
            6,
            "" if participant.sort_order is None else str(participant.sort_order),
        )
        self.participantTable.item(row, 0).setData(
            Qt.ItemDataRole.UserRole,
            participant.participant_id,
        )

    def _set_item(self, row: int, column: int, text: str) -> None:
        self.participantTable.setItem(row, column, QTableWidgetItem(text))

    def _row_participant_id(self, row: int) -> str:
        item = self.participantTable.item(row, 0)
        if item is not None:
            participant_id = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(participant_id, str) and participant_id:
                return participant_id
        return self._next_participant_id()

    def _next_participant_id(self) -> str:
        last_no = 0
        existing_ids = [participant.participant_id for participant in self.participants]
        for row in range(self.participantTable.rowCount()):
            item = self.participantTable.item(row, 0)
            if item is not None and isinstance(
                item.data(Qt.ItemDataRole.UserRole),
                str,
            ):
                existing_ids.append(item.data(Qt.ItemDataRole.UserRole))

        for participant_id in existing_ids:
            match = re.fullmatch(r"P-(\d{6})", participant_id)
            if match:
                last_no = max(last_no, int(match.group(1)))
        return f"P-{last_no + 1:06d}"

    def _cell_text(self, row: int, column: int) -> str:
        item = self.participantTable.item(row, column)
        if item is None:
            return ""
        return item.text().strip()

    def _is_active_cell(self, row: int) -> bool:
        text = self._cell_text(row, 0)
        if text == ACTIVE_TEXT:
            return True
        if text == INACTIVE_TEXT:
            return False
        raise ValueError("有効 must be 有効 or 無効")

    def _positive_int_cell(self, row: int, column: int, field_name: str) -> int:
        text = self._cell_text(row, column)
        if not text.isdecimal():
            raise ValueError(f"{field_name} must be an integer")
        value = int(text)
        if value < 1:
            raise ValueError(f"{field_name} must be at least 1")
        return value

    def _optional_positive_int_cell(
        self,
        row: int,
        column: int,
        field_name: str,
    ) -> int | None:
        text = self._cell_text(row, column)
        if not text:
            return None
        return self._positive_int_cell(row, column, field_name)

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)
