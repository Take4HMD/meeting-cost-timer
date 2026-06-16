import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication, QFileDialog

from app.models.participant import Participant
from app.models.role_rate import RoleRate
from app.windows.master_import_window import (
    TARGET_PARTICIPANTS,
    TARGET_ROLE_RATES,
    MasterImportWindow,
)


@pytest.fixture(scope="session")
def qt_application():
    application = QApplication.instance() or QApplication([])
    return application


class StubParticipantMasterService:
    def __init__(self, loaded_participants=None):
        self.loaded_participants = loaded_participants or []
        self.saved_participants = None
        self.saved_license_id = None
        self.loaded_license_id = None

    def load_participants(self, license_id):
        self.loaded_license_id = license_id
        return self.loaded_participants

    def save_participants(self, participants, license_id):
        self.saved_participants = participants
        self.saved_license_id = license_id


class StubRoleRateMasterService:
    def __init__(self, loaded_role_rates=None):
        self.loaded_role_rates = loaded_role_rates or []
        self.saved_role_rates = None
        self.saved_license_id = None
        self.loaded_license_id = None

    def load_role_rates(self, license_id):
        self.loaded_license_id = license_id
        return self.loaded_role_rates

    def save_role_rates(self, role_rates, license_id):
        self.saved_role_rates = role_rates
        self.saved_license_id = license_id


def _participant():
    return Participant(
        participant_id="P-000001",
        is_active=True,
        name="Yamada Taro",
        hourly_rate=6000,
    )


def _existing_participant(participant_id="P-000010", name="Existing User"):
    return Participant(
        participant_id=participant_id,
        is_active=True,
        name=name,
        hourly_rate=5000,
    )


def _role_rate():
    return RoleRate(
        role_rate_id="R-000001",
        is_active=True,
        role_name="Manager",
        hourly_rate=6000,
    )


def _existing_role_rate(role_rate_id="R-000010", role_name="Existing Role"):
    return RoleRate(
        role_rate_id=role_rate_id,
        is_active=True,
        role_name=role_name,
        hourly_rate=5000,
    )


def _window(
    participant_importer=None,
    role_rate_importer=None,
    participant_service=None,
    role_rate_service=None,
    settings=None,
):
    return MasterImportWindow(
        settings=settings or {"license_id": "LIC-TEST-001", "device_role": "master"},
        participant_master_service=participant_service or StubParticipantMasterService(),
        role_rate_master_service=role_rate_service or StubRoleRateMasterService(),
        participant_importer=participant_importer or (lambda file_path, device_role: []),
        role_rate_importer=role_rate_importer or (lambda file_path, device_role: []),
    )


def test_master_import_window_disables_controls_for_viewer(qt_application):
    window = _window(settings={"license_id": "LIC-TEST-001", "device_role": "viewer"})

    assert not window.importTargetComboBox.isEnabled()
    assert not window.importFileLineEdit.isEnabled()
    assert not window.browseButton.isEnabled()
    assert not window.templateExportButton.isEnabled()
    assert not window.importButton.isEnabled()
    assert not window.previewTable.isEnabled()
    window.close()


def test_master_import_window_selects_excel_file(qt_application, monkeypatch, tmp_path):
    window = _window()
    selected_path = str(tmp_path / "import.xlsx")
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (selected_path, "Excel Files (*.xlsx *.xlsm)"),
    )

    window.choose_excel_file()

    assert window.importFileLineEdit.text() == selected_path
    window.close()


def test_master_import_window_imports_and_saves_participants(qt_application, tmp_path):
    participant = _participant()
    participant_service = StubParticipantMasterService()
    imported_calls = []

    def participant_importer(file_path, device_role):
        imported_calls.append((file_path, device_role))
        return [participant]

    window = _window(
        participant_importer=participant_importer,
        participant_service=participant_service,
    )
    messages = []
    window._show_information = lambda title, message: messages.append((title, message))
    window._show_error = pytest.fail
    excel_path = tmp_path / "participants.xlsx"
    window.importFileLineEdit.setText(str(excel_path))
    window.importTargetComboBox.setCurrentIndex(
        window.importTargetComboBox.findData(TARGET_PARTICIPANTS)
    )

    window.importButton.click()

    assert imported_calls == [(Path(str(excel_path)), "master")]
    assert participant_service.loaded_license_id == "LIC-TEST-001"
    assert participant_service.saved_participants == [participant]
    assert participant_service.saved_license_id == "LIC-TEST-001"
    assert messages
    assert window.previewTable.item(0, 0).text() == "新規追加件数"
    assert window.previewTable.item(0, 1).text() == "1"
    assert window.previewTable.item(2, 1).text() == "0"
    window.close()


def test_master_import_window_imports_and_saves_role_rates(qt_application, tmp_path):
    role_rate = _role_rate()
    role_rate_service = StubRoleRateMasterService()
    imported_calls = []

    def role_rate_importer(file_path, device_role):
        imported_calls.append((file_path, device_role))
        return [role_rate]

    window = _window(
        role_rate_importer=role_rate_importer,
        role_rate_service=role_rate_service,
    )
    messages = []
    window._show_information = lambda title, message: messages.append((title, message))
    window._show_error = pytest.fail
    excel_path = tmp_path / "role_rates.xlsx"
    window.importFileLineEdit.setText(str(excel_path))
    window.importTargetComboBox.setCurrentIndex(
        window.importTargetComboBox.findData(TARGET_ROLE_RATES)
    )

    window.importButton.click()

    assert imported_calls == [(Path(str(excel_path)), "master")]
    assert role_rate_service.loaded_license_id == "LIC-TEST-001"
    assert role_rate_service.saved_role_rates == [role_rate]
    assert role_rate_service.saved_license_id == "LIC-TEST-001"
    assert messages
    assert window.previewTable.item(0, 1).text() == "1"
    window.close()


def test_master_import_window_shows_error_when_import_fails(qt_application, tmp_path):
    errors = []

    def participant_importer(file_path, device_role):
        raise ValueError("invalid import")

    participant_service = StubParticipantMasterService()
    window = _window(
        participant_importer=participant_importer,
        participant_service=participant_service,
    )
    window._show_error = lambda title, message: errors.append((title, message))
    window.importFileLineEdit.setText(str(tmp_path / "participants.xlsx"))
    window.importTargetComboBox.setCurrentIndex(
        window.importTargetComboBox.findData(TARGET_PARTICIPANTS)
    )

    window.importButton.click()

    assert errors
    assert participant_service.saved_participants is None
    assert window.previewTable.item(2, 1).text() == "1"
    window.close()


def test_master_import_window_merges_participants_with_existing_master(
    qt_application,
    tmp_path,
):
    existing = _existing_participant(name="Yamada Taro")
    imported = Participant(
        participant_id="P-000001",
        is_active=True,
        name="Yamada Taro",
        hourly_rate=8000,
    )
    participant_service = StubParticipantMasterService(
        loaded_participants=[
            existing,
            _existing_participant(participant_id="P-000011", name="Keep User"),
        ]
    )
    window = _window(
        participant_importer=lambda file_path, device_role: [imported],
        participant_service=participant_service,
    )
    window._show_information = lambda title, message: None
    window._show_error = pytest.fail
    window.importFileLineEdit.setText(str(tmp_path / "participants.xlsx"))
    window.importTargetComboBox.setCurrentIndex(
        window.importTargetComboBox.findData(TARGET_PARTICIPANTS)
    )

    window.importButton.click()

    assert participant_service.saved_participants == [
        Participant(
            participant_id="P-000010",
            is_active=True,
            name="Yamada Taro",
            hourly_rate=8000,
        ),
        _existing_participant(participant_id="P-000011", name="Keep User"),
    ]
    assert window.previewTable.item(0, 1).text() == "0"
    assert window.previewTable.item(1, 1).text() == "1"
    assert window.previewTable.item(2, 1).text() == "0"
    window.close()


def test_master_import_window_merges_role_rates_with_existing_master(
    qt_application,
    tmp_path,
):
    imported = RoleRate(
        role_rate_id="R-000001",
        is_active=True,
        role_name="Manager",
        hourly_rate=8000,
    )
    role_rate_service = StubRoleRateMasterService(
        loaded_role_rates=[
            _existing_role_rate(role_name="Manager"),
            _existing_role_rate(role_rate_id="R-000011", role_name="Keep Role"),
        ]
    )
    window = _window(
        role_rate_importer=lambda file_path, device_role: [imported],
        role_rate_service=role_rate_service,
    )
    window._show_information = lambda title, message: None
    window._show_error = pytest.fail
    window.importFileLineEdit.setText(str(tmp_path / "role_rates.xlsx"))
    window.importTargetComboBox.setCurrentIndex(
        window.importTargetComboBox.findData(TARGET_ROLE_RATES)
    )

    window.importButton.click()

    assert role_rate_service.saved_role_rates == [
        RoleRate(
            role_rate_id="R-000010",
            is_active=True,
            role_name="Manager",
            hourly_rate=8000,
        ),
        _existing_role_rate(role_rate_id="R-000011", role_name="Keep Role"),
    ]
    assert window.previewTable.item(0, 1).text() == "0"
    assert window.previewTable.item(1, 1).text() == "1"
    assert window.previewTable.item(2, 1).text() == "0"
    window.close()
