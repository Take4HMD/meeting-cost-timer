from __future__ import annotations

from pathlib import Path
import re
from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem

from app.models.participant import Participant
from app.services.license_settings_service import DEVICE_ROLE_VIEWER
from app.services.master_import_merge_service import merge_imported_participants
from app.services.participant_csv_import_service import import_participants_from_csv
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
        participant_csv_importer: Callable[[Path], list[Participant]]
        = import_participants_from_csv,
    ) -> None:
        super().__init__()
        self.settings = settings or {}
        self.participant_master_service = (
            participant_master_service or ParticipantMasterService()
        )
        self.participant_csv_importer = participant_csv_importer
        self.participants: list[Participant] = []
        self._saved_table_snapshot: tuple[tuple[str, ...], ...] = ()

        self.addRowButton.clicked.connect(self.add_row)
        self.deleteRowButton.clicked.connect(self.delete_selected_rows)
        self.saveButton.clicked.connect(self.save_participants)
        self.csvImportButton.clicked.connect(self.import_csv)
        self.closeButton.clicked.connect(self.request_close)
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
            if self.participantTable.rowCount() == 0:
                self.add_empty_row()
            self._saved_table_snapshot = self._table_snapshot()
        except Exception:
            self._show_error("参加者マスタ", "参加者マスタの読込に失敗しました。")
            self.set_participants([])
            self._saved_table_snapshot = self._table_snapshot()

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
        self._focus_participant_cell(row, 0)

    def add_row(self) -> None:
        blank_row = self._first_blank_input_row()
        if blank_row is not None:
            self._show_error("参加者マスタ", "未入力の行があります。")
            self._focus_participant_cell(blank_row, 0)
            return

        self.add_empty_row()

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

    def import_csv(self) -> None:
        file_path = self._select_csv_file()
        if file_path is None:
            return

        try:
            existing_participants = self._collect_non_blank_participants()
            imported_participants = self.participant_csv_importer(file_path)
            merge_result = merge_imported_participants(
                existing_participants,
                imported_participants,
            )
        except Exception:
            self._show_error("参加者マスタ", "CSV取込に失敗しました。")
            return

        self.set_participants(merge_result.items)
        if self.participantTable.rowCount() == 0:
            self.add_empty_row()
        else:
            self._focus_participant_cell(0, 0)
        self._show_info(
            "参加者マスタ",
            f"CSV取込が完了しました。追加: {merge_result.added_count}件、更新: {merge_result.updated_count}件",
        )

    def save_participants(self) -> bool:
        try:
            participants = self.collect_participants()
            self.participant_master_service.save_participants(
                participants,
                self.settings.get("license_id", ""),
            )
        except Exception:
            self._show_error("参加者マスタ", "参加者マスタの保存に失敗しました。")
            return False

        self.participants = participants
        self._saved_table_snapshot = self._table_snapshot()
        self._show_info("参加者マスタ", "保存しました。")
        return True

    def request_close(self) -> None:
        self.close()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._can_close_with_unsaved_changes_check():
            event.accept()
            return

        event.ignore()

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

    def _focus_participant_cell(self, row: int, column: int) -> None:
        item = self.participantTable.item(row, column)
        if item is None:
            return

        self.participantTable.setCurrentCell(row, column)
        self.participantTable.scrollToItem(item)
        self.participantTable.setFocus(Qt.FocusReason.OtherFocusReason)

    def _first_blank_input_row(self) -> int | None:
        for row in range(self.participantTable.rowCount()):
            if all(not self._cell_text(row, column) for column in range(1, 7)):
                return row
        return None

    def _can_close_with_unsaved_changes_check(self) -> bool:
        changed_cell = self._first_changed_cell()
        if changed_cell is None:
            return True

        reply = self._confirm_save_changes()
        if reply == QMessageBox.StandardButton.Yes:
            return self.save_participants()
        if reply == QMessageBox.StandardButton.No:
            return True

        self._focus_participant_cell(*changed_cell)
        return False

    def _first_changed_cell(self) -> tuple[int, int] | None:
        saved_snapshot = self._saved_table_snapshot
        current_snapshot = self._table_snapshot()
        max_rows = max(len(saved_snapshot), len(current_snapshot))

        for row in range(max_rows):
            saved_row = saved_snapshot[row] if row < len(saved_snapshot) else ()
            current_row = current_snapshot[row] if row < len(current_snapshot) else ()
            max_columns = max(len(saved_row), len(current_row))
            for column in range(max_columns):
                saved_value = saved_row[column] if column < len(saved_row) else ""
                current_value = current_row[column] if column < len(current_row) else ""
                if saved_value != current_value:
                    return (
                        min(row, max(self.participantTable.rowCount() - 1, 0)),
                        min(column, max(self.participantTable.columnCount() - 1, 0)),
                    )
        return None

    def _table_snapshot(self) -> tuple[tuple[str, ...], ...]:
        return tuple(
            tuple(self._cell_text(row, column) for column in range(7))
            for row in range(self.participantTable.rowCount())
        )

    def _collect_non_blank_participants(self) -> list[Participant]:
        participants = []
        for row in range(self.participantTable.rowCount()):
            if all(not self._cell_text(row, column) for column in range(1, 7)):
                continue
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

    def _select_csv_file(self) -> Path | None:
        file_name, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "CSVファイルを選択",
            "",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not file_name:
            return None
        return Path(file_name)

    def _confirm_save_changes(self) -> QMessageBox.StandardButton:
        return QMessageBox.question(
            self,
            "参加者マスタ",
            "保存されていない変更があります。保存しますか？",
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel
            ),
            QMessageBox.StandardButton.Yes,
        )

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

    def _show_info(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)
