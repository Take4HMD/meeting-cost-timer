from __future__ import annotations

import re

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem

from app.models.role_rate import RoleRate
from app.services.role_rate_master_service import RoleRateMasterService
from app.windows.base_window import UiWindow


ACTIVE_TEXT = "有効"
INACTIVE_TEXT = "無効"


class RoleRateMasterWindow(UiWindow):
    ui_file_name = "role_rate_master.ui"

    def __init__(
        self,
        settings: dict | None = None,
        role_rate_master_service: RoleRateMasterService | None = None,
    ) -> None:
        super().__init__()
        self.settings = settings or {}
        self.role_rate_master_service = (
            role_rate_master_service or RoleRateMasterService()
        )
        self.role_rates: list[RoleRate] = []

        self.addRowButton.clicked.connect(self.add_empty_row)
        self.deleteRowButton.clicked.connect(self.delete_selected_rows)
        self.saveButton.clicked.connect(self.save_role_rates)
        self.closeButton.clicked.connect(self.close)
        self.load_role_rates()

    def load_role_rates(self) -> None:
        license_id = self.settings.get("license_id", "")
        if not license_id:
            self.set_role_rates([])
            return

        try:
            self.set_role_rates(
                self.role_rate_master_service.load_role_rates(license_id)
            )
        except Exception as exc:
            self._show_error("役職単価マスタ", "役職単価マスタの読込に失敗しました。")
            self.set_role_rates([])

    def set_role_rates(self, role_rates: list[RoleRate]) -> None:
        self.role_rates = role_rates
        self.roleRateTable.setRowCount(0)
        for role_rate in role_rates:
            self._append_role_rate_row(role_rate)

    def add_empty_row(self) -> None:
        row = self.roleRateTable.rowCount()
        self.roleRateTable.insertRow(row)
        self._set_item(row, 0, ACTIVE_TEXT)
        self._set_item(row, 1, "")
        self._set_item(row, 2, "")
        self._set_item(row, 3, "")
        self.roleRateTable.item(row, 0).setData(
            Qt.ItemDataRole.UserRole,
            self._next_role_rate_id(),
        )

    def delete_selected_rows(self) -> None:
        selected_rows = {
            index.row() for index in self.roleRateTable.selectionModel().selectedRows()
        }
        if not selected_rows:
            current_row = self.roleRateTable.currentRow()
            if current_row >= 0:
                selected_rows.add(current_row)

        for row in sorted(selected_rows, reverse=True):
            self.roleRateTable.removeRow(row)

    def save_role_rates(self) -> None:
        try:
            role_rates = self.collect_role_rates()
            self.role_rate_master_service.save_role_rates(
                role_rates,
                self.settings.get("license_id", ""),
            )
        except Exception as exc:
            self._show_error("役職単価マスタ", "役職単価マスタの保存に失敗しました。")
            return

        self.role_rates = role_rates

    def collect_role_rates(self) -> list[RoleRate]:
        role_rates = []
        for row in range(self.roleRateTable.rowCount()):
            role_rates.append(
                RoleRate(
                    role_rate_id=self._row_role_rate_id(row),
                    is_active=self._is_active_cell(row),
                    role_name=self._cell_text(row, 1),
                    hourly_rate=self._positive_int_cell(row, 2, "概算時間単価"),
                    sort_order=self._optional_positive_int_cell(row, 3, "表示順"),
                )
            )
        return role_rates

    def _append_role_rate_row(self, role_rate: RoleRate) -> None:
        row = self.roleRateTable.rowCount()
        self.roleRateTable.insertRow(row)
        self._set_item(row, 0, ACTIVE_TEXT if role_rate.is_active else INACTIVE_TEXT)
        self._set_item(row, 1, role_rate.role_name)
        self._set_item(row, 2, str(role_rate.hourly_rate))
        self._set_item(
            row,
            3,
            "" if role_rate.sort_order is None else str(role_rate.sort_order),
        )
        self.roleRateTable.item(row, 0).setData(
            Qt.ItemDataRole.UserRole,
            role_rate.role_rate_id,
        )

    def _set_item(self, row: int, column: int, text: str) -> None:
        self.roleRateTable.setItem(row, column, QTableWidgetItem(text))

    def _row_role_rate_id(self, row: int) -> str:
        item = self.roleRateTable.item(row, 0)
        if item is not None:
            role_rate_id = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(role_rate_id, str) and role_rate_id:
                return role_rate_id
        return self._next_role_rate_id()

    def _next_role_rate_id(self) -> str:
        last_no = 0
        existing_ids = [role_rate.role_rate_id for role_rate in self.role_rates]
        for row in range(self.roleRateTable.rowCount()):
            item = self.roleRateTable.item(row, 0)
            if item is not None and isinstance(
                item.data(Qt.ItemDataRole.UserRole),
                str,
            ):
                existing_ids.append(item.data(Qt.ItemDataRole.UserRole))

        for role_rate_id in existing_ids:
            match = re.fullmatch(r"R-(\d{6})", role_rate_id)
            if match:
                last_no = max(last_no, int(match.group(1)))
        return f"R-{last_no + 1:06d}"

    def _cell_text(self, row: int, column: int) -> str:
        item = self.roleRateTable.item(row, column)
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
