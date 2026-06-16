import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication, QFileDialog

from app.models.participant import Participant
from app.models.role_rate import RoleRate
from app.services.master_excel_export_service import (
    PARTICIPANT_MASTER_EXPORT_FILE_NAME,
    ROLE_RATE_MASTER_EXPORT_FILE_NAME,
)
from app.windows.master_export_window import (
    TARGET_PARTICIPANTS,
    TARGET_ROLE_RATES,
    MasterExportWindow,
)


@pytest.fixture(scope="session")
def qt_application():
    application = QApplication.instance() or QApplication([])
    return application


class StubParticipantMasterService:
    def __init__(self, participants=None):
        self.participants = participants or []
        self.loaded_license_id = None

    def load_participants(self, license_id):
        self.loaded_license_id = license_id
        return self.participants


class StubRoleRateMasterService:
    def __init__(self, role_rates=None):
        self.role_rates = role_rates or []
        self.loaded_license_id = None

    def load_role_rates(self, license_id):
        self.loaded_license_id = license_id
        return self.role_rates


def _participant():
    return Participant(
        participant_id="P-000001",
        is_active=True,
        name="Yamada Taro",
        hourly_rate=6000,
    )


def _role_rate():
    return RoleRate(
        role_rate_id="R-000001",
        is_active=True,
        role_name="Manager",
        hourly_rate=6000,
    )


def _window(
    participant_service=None,
    role_rate_service=None,
    participant_exporter=None,
    role_rate_exporter=None,
    settings=None,
):
    return MasterExportWindow(
        settings=settings or {"license_id": "LIC-TEST-001", "device_role": "master"},
        participant_master_service=participant_service
        or StubParticipantMasterService(),
        role_rate_master_service=role_rate_service or StubRoleRateMasterService(),
        participant_exporter=participant_exporter or (lambda items, output_path: None),
        role_rate_exporter=role_rate_exporter or (lambda items, output_path: None),
    )


def test_master_export_window_disables_controls_for_viewer(qt_application):
    window = _window(settings={"license_id": "LIC-TEST-001", "device_role": "viewer"})

    assert not window.exportTargetComboBox.isEnabled()
    assert not window.exportFolderLineEdit.isEnabled()
    assert not window.browseButton.isEnabled()
    assert not window.openExplorerButton.isEnabled()
    assert not window.exportButton.isEnabled()
    window.close()


def test_master_export_window_selects_output_folder(qt_application, monkeypatch, tmp_path):
    window = _window()
    selected_path = str(tmp_path / "exports")
    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: selected_path,
    )

    window.choose_output_folder()

    assert window.exportFolderLineEdit.text() == selected_path
    window.close()


def test_master_export_window_loads_and_exports_participants(qt_application, tmp_path):
    participant = _participant()
    participant_service = StubParticipantMasterService([participant])
    export_calls = []

    def participant_exporter(items, output_path):
        export_calls.append((items, output_path))

    window = _window(
        participant_service=participant_service,
        participant_exporter=participant_exporter,
    )
    messages = []
    window._show_information = lambda title, message: messages.append((title, message))
    window._show_error = pytest.fail
    window.exportFolderLineEdit.setText(str(tmp_path))
    window.exportTargetComboBox.setCurrentIndex(
        window.exportTargetComboBox.findData(TARGET_PARTICIPANTS)
    )

    window.exportButton.click()

    assert participant_service.loaded_license_id == "LIC-TEST-001"
    assert export_calls == [
        ([participant], Path(str(tmp_path)) / PARTICIPANT_MASTER_EXPORT_FILE_NAME)
    ]
    assert messages
    window.close()


def test_master_export_window_loads_and_exports_role_rates(qt_application, tmp_path):
    role_rate = _role_rate()
    role_rate_service = StubRoleRateMasterService([role_rate])
    export_calls = []

    def role_rate_exporter(items, output_path):
        export_calls.append((items, output_path))

    window = _window(
        role_rate_service=role_rate_service,
        role_rate_exporter=role_rate_exporter,
    )
    messages = []
    window._show_information = lambda title, message: messages.append((title, message))
    window._show_error = pytest.fail
    window.exportFolderLineEdit.setText(str(tmp_path))
    window.exportTargetComboBox.setCurrentIndex(
        window.exportTargetComboBox.findData(TARGET_ROLE_RATES)
    )

    window.exportButton.click()

    assert role_rate_service.loaded_license_id == "LIC-TEST-001"
    assert export_calls == [
        ([role_rate], Path(str(tmp_path)) / ROLE_RATE_MASTER_EXPORT_FILE_NAME)
    ]
    assert messages
    window.close()


def test_master_export_window_shows_error_when_export_fails(qt_application, tmp_path):
    errors = []

    def participant_exporter(items, output_path):
        raise ValueError("export failed")

    window = _window(
        participant_service=StubParticipantMasterService([_participant()]),
        participant_exporter=participant_exporter,
    )
    window._show_error = lambda title, message: errors.append((title, message))
    window.exportFolderLineEdit.setText(str(tmp_path))
    window.exportTargetComboBox.setCurrentIndex(
        window.exportTargetComboBox.findData(TARGET_PARTICIPANTS)
    )

    window.exportButton.click()

    assert errors
    window.close()
