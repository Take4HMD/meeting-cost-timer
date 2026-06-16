from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import QFileDialog, QMessageBox

from app.models.meeting import MeetingResult
from app.services.csv_export_service import export_meeting_result_csv
from app.services.settings_service import SettingsService
from app.utils.logging_config import configure_error_logging, log_exception
from app.windows.base_window import UiWindow


OUTPUT_FORMAT_CSV = "csv"


class ResultExportWindow(UiWindow):
    ui_file_name = "result_export.ui"

    def __init__(
        self,
        meeting_result: MeetingResult | None = None,
        settings: dict | None = None,
        settings_service: SettingsService | None = None,
        csv_exporter: Callable[[MeetingResult, Path], None] = export_meeting_result_csv,
        now_provider: Callable[[], datetime] | None = None,
        exception_logger: Callable[[str, Exception, str | Path | None, object], None]
        = log_exception,
    ) -> None:
        super().__init__()
        self.meeting_result = meeting_result
        self.settings = settings or {}
        self.settings_service = settings_service
        self.csv_exporter = csv_exporter
        self.now_provider = now_provider or datetime.now
        self.exception_logger = exception_logger

        self._configure_output_format_combo_box()
        self._apply_initial_output_folder()
        self.browseButton.clicked.connect(self.choose_output_folder)
        self.exportButton.clicked.connect(self.execute_export)
        self.closeButton.clicked.connect(self.close)

    def choose_output_folder(self) -> None:
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "出力先フォルダ選択",
            self.outputFolderLineEdit.text().strip(),
        )
        if folder_path:
            self.outputFolderLineEdit.setText(folder_path)

    def execute_export(self) -> Path | None:
        output_path: Path | None = None
        try:
            if self.meeting_result is None:
                raise ValueError("meeting_result is required")
            if self.outputFormatComboBox.currentData() != OUTPUT_FORMAT_CSV:
                raise ValueError("output format is invalid")

            output_folder = self._selected_output_folder()
            output_path = output_folder / self._csv_file_name()
            self.csv_exporter(self.meeting_result, output_path)
            self._save_last_output_dir(output_folder)
        except Exception as exc:
            logger = configure_error_logging()
            self.exception_logger("result_export", exc, output_path, logger)
            self._show_error("結果出力", "結果出力に失敗しました。")
            return None

        self._show_information("結果出力", "結果出力が完了しました。")
        return output_path

    def _configure_output_format_combo_box(self) -> None:
        self.outputFormatComboBox.clear()
        self.outputFormatComboBox.addItem("CSV", OUTPUT_FORMAT_CSV)
        self.outputFormatComboBox.setEnabled(False)

    def _apply_initial_output_folder(self) -> None:
        output_settings = self.settings.get("output_settings", {})
        last_output_dir = output_settings.get("last_output_dir", "")
        if last_output_dir and Path(last_output_dir).is_dir():
            self.outputFolderLineEdit.setText(last_output_dir)

    def _selected_output_folder(self) -> Path:
        folder_path_text = self.outputFolderLineEdit.text().strip()
        if not folder_path_text:
            raise ValueError("output folder is required")
        return Path(folder_path_text)

    def _csv_file_name(self) -> str:
        timestamp = self.now_provider().strftime("%Y%m%d_%H%M%S")
        return f"meeting_cost_{timestamp}.csv"

    def _save_last_output_dir(self, output_folder: Path) -> None:
        output_settings = self.settings.setdefault("output_settings", {})
        output_settings["last_output_dir"] = str(output_folder)
        output_settings.setdefault("default_format", OUTPUT_FORMAT_CSV)
        if self.settings_service is not None:
            self.settings_service.save(self.settings)

    def _show_information(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)
