from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem

from app.services.excel_import_service import (
    import_participants_from_excel,
    import_role_rates_from_excel,
)
from app.services.license_settings_service import DEVICE_ROLE_VIEWER
from app.services.master_import_merge_service import (
    merge_imported_participants,
    merge_imported_role_rates,
)
from app.services.participant_master_service import ParticipantMasterService
from app.services.role_rate_master_service import RoleRateMasterService
from app.windows.base_window import UiWindow


TARGET_PARTICIPANTS = "participants"
TARGET_ROLE_RATES = "role_rates"


class MasterImportWindow(UiWindow):
    ui_file_name = "master_import.ui"

    def __init__(
        self,
        settings: dict | None = None,
        participant_master_service: ParticipantMasterService | None = None,
        role_rate_master_service: RoleRateMasterService | None = None,
        participant_importer=import_participants_from_excel,
        role_rate_importer=import_role_rates_from_excel,
    ) -> None:
        super().__init__()
        self.settings = settings or {}
        self.participant_master_service = (
            participant_master_service or ParticipantMasterService()
        )
        self.role_rate_master_service = role_rate_master_service or RoleRateMasterService()
        self.participant_importer = participant_importer
        self.role_rate_importer = role_rate_importer

        self._configure_import_target_combo_box()
        self.browseButton.clicked.connect(self.choose_excel_file)
        self.importButton.clicked.connect(self.execute_import)
        self.closeButton.clicked.connect(self.close)
        self.apply_device_role()

    def apply_device_role(self) -> None:
        if self.settings.get("device_role") != DEVICE_ROLE_VIEWER:
            return

        self.importTargetComboBox.setEnabled(False)
        self.importFileLineEdit.setEnabled(False)
        self.browseButton.setEnabled(False)
        self.templateExportButton.setEnabled(False)
        self.importButton.setEnabled(False)
        self.previewTable.setEnabled(False)

    def choose_excel_file(self) -> None:
        file_path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Excelファイル選択",
            "",
            "Excel Files (*.xlsx *.xlsm)",
        )
        if file_path:
            self.importFileLineEdit.setText(file_path)

    def execute_import(self) -> None:
        try:
            file_path = self._selected_file_path()
            license_id = self._license_id()
            device_role = self.settings.get("device_role", "")
            target = self.importTargetComboBox.currentData()

            if target == TARGET_PARTICIPANTS:
                imported_items = self.participant_importer(file_path, device_role)
                existing_items = self.participant_master_service.load_participants(
                    license_id,
                )
                merge_result = merge_imported_participants(
                    existing_items,
                    imported_items,
                )
                self.participant_master_service.save_participants(
                    merge_result.items,
                    license_id,
                )
            elif target == TARGET_ROLE_RATES:
                imported_items = self.role_rate_importer(file_path, device_role)
                existing_items = self.role_rate_master_service.load_role_rates(
                    license_id,
                )
                merge_result = merge_imported_role_rates(
                    existing_items,
                    imported_items,
                )
                self.role_rate_master_service.save_role_rates(
                    merge_result.items,
                    license_id,
                )
            else:
                raise ValueError("import target is invalid")
        except Exception:
            self._set_preview_counts(0, 0, 1)
            self._show_error("マスタ取込", "マスタ取込に失敗しました。")
            return

        self._set_preview_counts(
            merge_result.added_count,
            merge_result.updated_count,
            merge_result.error_count,
        )
        self._show_information("マスタ取込", "マスタ取込が完了しました。")

    def _configure_import_target_combo_box(self) -> None:
        self.importTargetComboBox.clear()
        self.importTargetComboBox.addItem("参加者マスタ", TARGET_PARTICIPANTS)
        self.importTargetComboBox.addItem("役職単価マスタ", TARGET_ROLE_RATES)

    def _selected_file_path(self) -> Path:
        file_path_text = self.importFileLineEdit.text().strip()
        if not file_path_text:
            raise ValueError("import file is required")
        return Path(file_path_text)

    def _license_id(self) -> str:
        license_id = self.settings.get("license_id", "")
        if not license_id:
            raise ValueError("license_id is required")
        return license_id

    def _set_preview_counts(
        self,
        added_count: int,
        updated_count: int,
        error_count: int,
    ) -> None:
        rows = [
            ("新規追加件数", str(added_count)),
            ("更新件数", str(updated_count)),
            ("エラー件数", str(error_count)),
        ]
        self.previewTable.setRowCount(0)
        for row_index, (label, value) in enumerate(rows):
            self.previewTable.insertRow(row_index)
            self.previewTable.setItem(row_index, 0, QTableWidgetItem(label))
            self.previewTable.setItem(row_index, 1, QTableWidgetItem(value))

    def _show_information(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)
