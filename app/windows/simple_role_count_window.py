from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem

from app.models.role_rate import RoleRate
from app.services.calculation_service import calculate_simple_total_hourly_rate
from app.services.role_rate_master_service import RoleRateMasterService
from app.windows.base_window import UiWindow


class SimpleRoleCountWindow(UiWindow):
    ui_file_name = "simple_role_count.ui"

    def __init__(
        self,
        settings: dict | None = None,
        role_rate_master_service: RoleRateMasterService | None = None,
        on_confirm: Callable[[int], None] | None = None,
        calculator=calculate_simple_total_hourly_rate,
    ) -> None:
        super().__init__()
        self.settings = settings or {}
        self.role_rate_master_service = (
            role_rate_master_service or RoleRateMasterService()
        )
        self.on_confirm = on_confirm
        self.calculator = calculator
        self.role_rates: list[RoleRate] = []

        self.confirmButton.clicked.connect(self.confirm_input)
        self.clearButton.clicked.connect(self.clear_counts)
        self.closeButton.clicked.connect(self.close)
        self.load_role_rates()

    def load_role_rates(self) -> None:
        license_id = self.settings.get("license_id", "")
        if not license_id:
            self.set_role_rates([])
            return

        try:
            loaded_role_rates = self.role_rate_master_service.load_role_rates(
                license_id
            )
        except Exception:
            self._show_error(
                "簡易モード",
                "役職単価マスタの読込に失敗しました。",
            )
            self.set_role_rates([])
            return

        self.set_role_rates(
            [role_rate for role_rate in loaded_role_rates if role_rate.is_active]
        )

    def set_role_rates(self, role_rates: list[RoleRate]) -> None:
        self.role_rates = role_rates
        self.roleCountTable.setRowCount(0)
        for role_rate in role_rates:
            self._append_role_rate_row(role_rate)

    def confirm_input(self) -> int | None:
        try:
            total_hourly_rate = self.calculator(self.collect_role_rate_counts())
        except Exception:
            self._show_error(
                "簡易モード",
                "人数は0以上の整数で入力し、1名以上を指定してください。",
            )
            return None

        if self.on_confirm is not None:
            self.on_confirm(total_hourly_rate)
        self.close()
        return total_hourly_rate

    def collect_role_rate_counts(self) -> list[tuple[RoleRate, int]]:
        role_rate_counts = []
        for row in range(self.roleCountTable.rowCount()):
            count = self._non_negative_int_cell(row, 1)
            if count > 0:
                role_rate_counts.append((self._row_role_rate(row), count))
        return role_rate_counts

    def clear_counts(self) -> None:
        for row in range(self.roleCountTable.rowCount()):
            self._set_item(row, 1, "0")

    def _append_role_rate_row(self, role_rate: RoleRate) -> None:
        row = self.roleCountTable.rowCount()
        self.roleCountTable.insertRow(row)
        self._set_item(row, 0, role_rate.role_name)
        self._set_item(row, 1, "0")
        self.roleCountTable.item(row, 0).setData(
            Qt.ItemDataRole.UserRole,
            role_rate,
        )

    def _row_role_rate(self, row: int) -> RoleRate:
        item = self.roleCountTable.item(row, 0)
        if item is None:
            raise ValueError("role_rate is required")
        role_rate = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(role_rate, RoleRate):
            raise ValueError("role_rate is invalid")
        return role_rate

    def _set_item(self, row: int, column: int, text: str) -> None:
        self.roleCountTable.setItem(row, column, QTableWidgetItem(text))

    def _cell_text(self, row: int, column: int) -> str:
        item = self.roleCountTable.item(row, column)
        if item is None:
            return ""
        return item.text().strip()

    def _non_negative_int_cell(self, row: int, column: int) -> int:
        text = self._cell_text(row, column)
        if not text.isdecimal():
            raise ValueError("count must be an integer")
        return int(text)

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)
