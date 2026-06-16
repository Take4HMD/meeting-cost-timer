from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QFileDialog, QMessageBox

from app.services.license_settings_service import DEVICE_ROLE_VIEWER
from app.services.master_excel_export_service import (
    PARTICIPANT_MASTER_EXPORT_FILE_NAME,
    ROLE_RATE_MASTER_EXPORT_FILE_NAME,
    export_participants_to_excel,
    export_role_rates_to_excel,
)
from app.services.participant_master_service import ParticipantMasterService
from app.services.role_rate_master_service import RoleRateMasterService
from app.windows.base_window import UiWindow


TARGET_PARTICIPANTS = "participants"
TARGET_ROLE_RATES = "role_rates"


class MasterExportWindow(UiWindow):
    ui_file_name = "master_export.ui"

    def __init__(
        self,
        settings: dict | None = None,
        participant_master_service: ParticipantMasterService | None = None,
        role_rate_master_service: RoleRateMasterService | None = None,
        participant_exporter=export_participants_to_excel,
        role_rate_exporter=export_role_rates_to_excel,
    ) -> None:
        super().__init__()
        self.settings = settings or {}
        self.participant_master_service = (
            participant_master_service or ParticipantMasterService()
        )
        self.role_rate_master_service = role_rate_master_service or RoleRateMasterService()
        self.participant_exporter = participant_exporter
        self.role_rate_exporter = role_rate_exporter

        self._configure_export_target_combo_box()
        self.browseButton.clicked.connect(self.choose_output_folder)
        self.exportButton.clicked.connect(self.execute_export)
        self.closeButton.clicked.connect(self.close)
        self.apply_device_role()

    def apply_device_role(self) -> None:
        if self.settings.get("device_role") != DEVICE_ROLE_VIEWER:
            return

        self.exportTargetComboBox.setEnabled(False)
        self.exportFolderLineEdit.setEnabled(False)
        self.browseButton.setEnabled(False)
        self.openExplorerButton.setEnabled(False)
        self.exportButton.setEnabled(False)

    def choose_output_folder(self) -> None:
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "出力先フォルダ選択",
            "",
        )
        if folder_path:
            self.exportFolderLineEdit.setText(folder_path)

    def execute_export(self) -> None:
        try:
            output_folder = self._selected_output_folder()
            license_id = self._license_id()
            target = self.exportTargetComboBox.currentData()

            if target == TARGET_PARTICIPANTS:
                participants = self.participant_master_service.load_participants(
                    license_id,
                )
                self.participant_exporter(
                    participants,
                    output_folder / PARTICIPANT_MASTER_EXPORT_FILE_NAME,
                )
            elif target == TARGET_ROLE_RATES:
                role_rates = self.role_rate_master_service.load_role_rates(
                    license_id,
                )
                self.role_rate_exporter(
                    role_rates,
                    output_folder / ROLE_RATE_MASTER_EXPORT_FILE_NAME,
                )
            else:
                raise ValueError("export target is invalid")
        except Exception:
            self._show_error("マスタ出力", "マスタ出力に失敗しました。")
            return

        self._show_information("マスタ出力", "マスタ出力が完了しました。")

    def _configure_export_target_combo_box(self) -> None:
        self.exportTargetComboBox.clear()
        self.exportTargetComboBox.addItem("参加者マスタ", TARGET_PARTICIPANTS)
        self.exportTargetComboBox.addItem("役職単価マスタ", TARGET_ROLE_RATES)

    def _selected_output_folder(self) -> Path:
        folder_path_text = self.exportFolderLineEdit.text().strip()
        if not folder_path_text:
            raise ValueError("output folder is required")
        return Path(folder_path_text)

    def _license_id(self) -> str:
        license_id = self.settings.get("license_id", "")
        if not license_id:
            raise ValueError("license_id is required")
        return license_id

    def _show_information(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)
