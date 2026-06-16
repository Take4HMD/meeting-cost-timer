from __future__ import annotations

from app.services.license_settings_service import DEVICE_ROLE_VIEWER
from app.windows.base_window import UiWindow
from app.windows.master_export_window import MasterExportWindow
from app.windows.master_import_window import MasterImportWindow
from app.windows.participant_master_window import ParticipantMasterWindow
from app.windows.role_rate_master_window import RoleRateMasterWindow


class MasterMenuWindow(UiWindow):
    ui_file_name = "master_menu.ui"

    def __init__(
        self,
        settings: dict | None = None,
        destination_window_classes: dict[str, type] | None = None,
    ) -> None:
        super().__init__()
        self.settings = settings or {}
        self.destination_window_classes = destination_window_classes or {
            "participant_master": ParticipantMasterWindow,
            "role_rate_master": RoleRateMasterWindow,
            "master_import": MasterImportWindow,
            "master_export": MasterExportWindow,
        }
        self.opened_windows = []

        self.participantMasterButton.clicked.connect(
            lambda: self.open_destination_window("participant_master")
        )
        self.roleRateMasterButton.clicked.connect(
            lambda: self.open_destination_window("role_rate_master")
        )
        self.masterImportButton.clicked.connect(
            lambda: self.open_destination_window("master_import")
        )
        self.masterExportButton.clicked.connect(
            lambda: self.open_destination_window("master_export")
        )
        self.closeButton.clicked.connect(self.close)
        self.apply_device_role()

    def apply_device_role(self) -> None:
        if self.settings.get("device_role") != DEVICE_ROLE_VIEWER:
            return

        self.participantMasterButton.setEnabled(False)
        self.masterImportButton.setEnabled(False)
        self.masterExportButton.setEnabled(False)

    def open_destination_window(self, destination: str):
        window_class = self.destination_window_classes[destination]
        if destination in {
            "participant_master",
            "role_rate_master",
            "master_import",
            "master_export",
        }:
            window = window_class(settings=self.settings)
        else:
            window = window_class()
        self.opened_windows.append(window)
        window.show()
        return window
