from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PyQt6.QtWidgets import QFileDialog, QMessageBox

from app.models.meeting import MeetingStartSettings
from app.services.mcd_service import load_mcd
from app.windows.base_window import UiWindow


class McdImportWindow(UiWindow):
    ui_file_name = "mcd_import.ui"

    def __init__(
        self,
        settings: dict | None = None,
        on_load: Callable[[MeetingStartSettings], None] | None = None,
        mcd_loader=load_mcd,
    ) -> None:
        super().__init__()
        self.settings = settings or {}
        self.on_load = on_load
        self.mcd_loader = mcd_loader

        self.browseButton.clicked.connect(self.choose_mcd_file)
        self.loadButton.clicked.connect(self.load_display_data)
        self.closeButton.clicked.connect(self.close)

    def choose_mcd_file(self) -> None:
        file_path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "表示用データ選択",
            "",
            "MCD Files (*.mcd)",
        )
        if file_path:
            self.mcdFileLineEdit.setText(file_path)

    def load_display_data(self) -> MeetingStartSettings | None:
        try:
            mcd_file_path = self._selected_file_path()
            meeting_settings = self.mcd_loader(
                mcd_file_path,
                current_device_role=self._device_role(),
                current_license_id=self._license_id(),
            )
        except Exception:
            self._show_error(
                "表示用データ読込",
                "表示用データの読込に失敗しました。",
            )
            return None

        if self.on_load is not None:
            self.on_load(meeting_settings)
        self.close()
        return meeting_settings

    def _selected_file_path(self) -> Path:
        file_path_text = self.mcdFileLineEdit.text().strip()
        if not file_path_text:
            raise ValueError("mcd file is required")
        return Path(file_path_text)

    def _device_role(self) -> str:
        device_role = self.settings.get("device_role", "")
        if not device_role:
            raise ValueError("device_role is required")
        return device_role

    def _license_id(self) -> str:
        license_id = self.settings.get("license_id", "")
        if not license_id:
            raise ValueError("license_id is required")
        return license_id

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)
