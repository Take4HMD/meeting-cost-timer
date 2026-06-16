from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtWidgets import QMessageBox

from app.services.calculation_service import validate_direct_total_hourly_rate
from app.windows.base_window import UiWindow


class DirectInputWindow(UiWindow):
    ui_file_name = "direct_input.ui"

    def __init__(
        self,
        on_confirm: Callable[[int], None] | None = None,
    ) -> None:
        super().__init__()
        self.on_confirm = on_confirm

        self.confirmButton.clicked.connect(self.confirm_input)
        self.closeButton.clicked.connect(self.close)

    def confirm_input(self) -> int | None:
        try:
            total_hourly_rate = validate_direct_total_hourly_rate(
                self.totalHourlyRateLineEdit.text()
            )
        except ValueError:
            self._show_error("直接入力", "合算時間単価は1円以上の整数で入力してください。")
            return None

        if self.on_confirm is not None:
            self.on_confirm(total_hourly_rate)
        self.close()
        return total_hourly_rate

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)
