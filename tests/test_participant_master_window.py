import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox, QTableWidgetItem

from app.models.participant import Participant
from app.windows.participant_master_window import ParticipantMasterWindow


@pytest.fixture(scope="session")
def qt_application():
    application = QApplication.instance() or QApplication([])
    return application


class StubParticipantMasterService:
    def __init__(self, loaded_participants=None, load_error=None, save_error=None):
        self.loaded_participants = loaded_participants or []
        self.load_error = load_error
        self.save_error = save_error
        self.saved_participants = None
        self.saved_license_id = None

    def load_participants(self, license_id):
        if self.load_error is not None:
            raise self.load_error
        self.loaded_license_id = license_id
        return self.loaded_participants

    def save_participants(self, participants, license_id):
        if self.save_error is not None:
            raise self.save_error
        self.saved_participants = participants
        self.saved_license_id = license_id


def _participant(
    participant_id="P-000001",
    is_active=True,
    name="Yamada Taro",
    department="Sales",
    position="Manager",
    display_name="A",
    hourly_rate=6000,
    sort_order=1,
):
    return Participant(
        participant_id=participant_id,
        is_active=is_active,
        name=name,
        department=department,
        position=position,
        display_name=display_name,
        hourly_rate=hourly_rate,
        sort_order=sort_order,
    )


def test_participant_master_window_loads_participants_into_table(qt_application):
    service = StubParticipantMasterService(
        loaded_participants=[
            _participant(),
            _participant(
                participant_id="P-000002",
                is_active=False,
                name="Sato Hanako",
                department="",
                position="",
                display_name="",
                hourly_rate=4000,
                sort_order=None,
            ),
        ]
    )

    window = ParticipantMasterWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "master"},
        participant_master_service=service,
    )

    assert service.loaded_license_id == "LIC-TEST-001"
    assert window.participantTable.rowCount() == 2
    assert window.participantTable.item(0, 0).text() == "有効"
    assert window.participantTable.item(0, 1).text() == "Yamada Taro"
    assert window.participantTable.item(0, 2).text() == "Sales"
    assert window.participantTable.item(0, 3).text() == "Manager"
    assert window.participantTable.item(0, 4).text() == "A"
    assert window.participantTable.item(0, 5).text() == "6000"
    assert window.participantTable.item(0, 6).text() == "1"
    assert window.participantTable.item(1, 0).text() == "無効"
    assert window.participantTable.item(1, 6).text() == ""
    window.close()


def test_participant_master_window_adds_and_deletes_rows(qt_application):
    window = ParticipantMasterWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "master"},
        participant_master_service=StubParticipantMasterService(),
    )

    assert window.participantTable.rowCount() == 1
    assert window.participantTable.item(0, 0).text() == "有効"
    assert window.participantTable.currentRow() == 0
    assert window.participantTable.currentColumn() == 0

    window.participantTable.item(0, 1).setText("Yamada Taro")
    window.addRowButton.click()
    assert window.participantTable.rowCount() == 2
    assert window.participantTable.item(1, 0).text() == "有効"
    assert window.participantTable.item(1, 1).text() == ""
    assert window.participantTable.currentRow() == 1
    assert window.participantTable.currentColumn() == 0
    assert window.participantTable.currentItem() == window.participantTable.item(1, 0)

    window.participantTable.selectRow(1)
    window.deleteRowButton.click()

    assert window.participantTable.rowCount() == 1
    window._confirm_save_changes = lambda: QMessageBox.StandardButton.No
    window.close()


def test_participant_master_window_rejects_new_row_when_blank_row_exists(
    qt_application,
):
    errors = []
    window = ParticipantMasterWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "master"},
        participant_master_service=StubParticipantMasterService(),
    )
    window._show_error = lambda title, message: errors.append((title, message))

    window.addRowButton.click()

    assert errors == [("参加者マスタ", "未入力の行があります。")]
    assert window.participantTable.rowCount() == 1
    assert window.participantTable.currentRow() == 0
    assert window.participantTable.currentColumn() == 0
    assert window.participantTable.currentItem() == window.participantTable.item(0, 0)
    window.close()


def test_participant_master_window_imports_csv_and_merges_rows(qt_application, tmp_path):
    csv_path = tmp_path / "participants.csv"
    imported_participants = [
        Participant(
            participant_id="P-000001",
            is_active=True,
            name="Yamada Taro",
            department="Sales",
            position="Manager",
            display_name="A",
            hourly_rate=8000,
            sort_order=2,
        ),
        Participant(
            participant_id="P-000002",
            is_active=True,
            name="Suzuki Jiro",
            hourly_rate=5000,
        ),
    ]
    service = StubParticipantMasterService(
        loaded_participants=[_participant(participant_id="P-000010")]
    )
    messages = []
    window = ParticipantMasterWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "master"},
        participant_master_service=service,
        participant_csv_importer=lambda path: imported_participants,
    )
    window._select_csv_file = lambda: csv_path
    window._show_info = lambda title, message: messages.append((title, message))

    window.csvImportButton.click()

    assert window.participantTable.rowCount() == 2
    assert (
        window.participantTable.item(0, 0).data(Qt.ItemDataRole.UserRole)
        == "P-000010"
    )
    assert window.participantTable.item(0, 1).text() == "Yamada Taro"
    assert window.participantTable.item(0, 5).text() == "8000"
    assert (
        window.participantTable.item(1, 0).data(Qt.ItemDataRole.UserRole)
        == "P-000011"
    )
    assert window.participantTable.item(1, 1).text() == "Suzuki Jiro"
    assert window.participantTable.currentRow() == 0
    assert window.participantTable.currentColumn() == 0
    assert messages == [("参加者マスタ", "CSV取込が完了しました。追加: 1件、更新: 1件")]
    window._confirm_save_changes = lambda: QMessageBox.StandardButton.No
    window.close()


def test_participant_master_window_does_not_change_when_csv_selection_is_cancelled(
    qt_application,
):
    window = ParticipantMasterWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "master"},
        participant_master_service=StubParticipantMasterService(
            loaded_participants=[_participant()]
        ),
        participant_csv_importer=pytest.fail,
    )
    window._select_csv_file = lambda: None

    window.csvImportButton.click()

    assert window.participantTable.rowCount() == 1
    assert window.participantTable.item(0, 1).text() == "Yamada Taro"
    window.close()


def test_participant_master_window_shows_error_when_csv_import_fails(
    qt_application,
    tmp_path,
):
    errors = []
    window = ParticipantMasterWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "master"},
        participant_master_service=StubParticipantMasterService(),
        participant_csv_importer=lambda path: (_ for _ in ()).throw(ValueError()),
    )
    window._select_csv_file = lambda: tmp_path / "participants.csv"
    window._show_error = lambda title, message: errors.append((title, message))

    window.csvImportButton.click()

    assert errors == [("参加者マスタ", "CSV取込に失敗しました。")]
    assert window.participantTable.rowCount() == 1
    window.close()


def test_participant_master_window_saves_table_values(qt_application):
    service = StubParticipantMasterService(loaded_participants=[_participant()])
    window = ParticipantMasterWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "master"},
        participant_master_service=service,
    )

    window.participantTable.setItem(0, 1, QTableWidgetItem("Suzuki Jiro"))
    window.participantTable.setItem(0, 2, QTableWidgetItem("Dev"))
    window.participantTable.setItem(0, 3, QTableWidgetItem("Lead"))
    window.participantTable.setItem(0, 4, QTableWidgetItem(""))
    window.participantTable.setItem(0, 5, QTableWidgetItem("7000"))
    window.participantTable.setItem(0, 6, QTableWidgetItem(""))
    window._show_error = pytest.fail
    messages = []
    window._show_info = lambda title, message: messages.append((title, message))

    window.saveButton.click()

    assert service.saved_license_id == "LIC-TEST-001"
    assert service.saved_participants == [
        Participant(
            participant_id="P-000001",
            is_active=True,
            name="Suzuki Jiro",
            department="Dev",
            position="Lead",
            display_name="",
            hourly_rate=7000,
            sort_order=None,
        )
    ]
    assert messages == [("参加者マスタ", "保存しました。")]
    window.close()


def test_participant_master_window_shows_error_when_save_validation_fails(
    qt_application,
):
    service = StubParticipantMasterService(loaded_participants=[_participant()])
    errors = []
    window = ParticipantMasterWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "master"},
        participant_master_service=service,
    )
    window._show_error = lambda title, message: errors.append((title, message))

    window.participantTable.setItem(0, 5, QTableWidgetItem("0"))
    window.saveButton.click()

    assert errors
    assert service.saved_participants is None
    window._confirm_save_changes = lambda: QMessageBox.StandardButton.No
    window.close()


def test_participant_master_window_keeps_window_open_when_close_is_cancelled(
    qt_application,
):
    window = ParticipantMasterWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "master"},
        participant_master_service=StubParticipantMasterService(
            loaded_participants=[_participant()]
        ),
    )
    window.show()
    window.participantTable.item(0, 1).setText("Changed Name")
    window.participantTable.setCurrentCell(0, 2)
    window._confirm_save_changes = lambda: QMessageBox.StandardButton.Cancel

    window.request_close()

    assert window.isVisible()
    assert window.participantTable.currentRow() == 0
    assert window.participantTable.currentColumn() == 1
    window._confirm_save_changes = lambda: QMessageBox.StandardButton.No
    window.close()


def test_participant_master_window_closes_when_unsaved_changes_are_saved(
    qt_application,
):
    service = StubParticipantMasterService(loaded_participants=[_participant()])
    window = ParticipantMasterWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "master"},
        participant_master_service=service,
    )
    window.show()
    window.participantTable.item(0, 1).setText("Changed Name")
    window._show_info = lambda title, message: None
    window._confirm_save_changes = lambda: QMessageBox.StandardButton.Yes

    window.request_close()

    assert not window.isVisible()
    assert service.saved_participants[0].name == "Changed Name"


def test_participant_master_window_closes_when_unsaved_changes_are_discarded(
    qt_application,
):
    service = StubParticipantMasterService(loaded_participants=[_participant()])
    window = ParticipantMasterWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "master"},
        participant_master_service=service,
    )
    window.show()
    window.participantTable.item(0, 1).setText("Changed Name")
    window._confirm_save_changes = lambda: QMessageBox.StandardButton.No

    window.request_close()

    assert not window.isVisible()
    assert service.saved_participants is None


def test_participant_master_window_handles_load_error(qt_application):
    errors = []
    window = ParticipantMasterWindow(
        settings={},
        participant_master_service=StubParticipantMasterService(load_error=RuntimeError()),
    )
    window._show_error = lambda title, message: errors.append((title, message))
    window.settings = {"license_id": "LIC-TEST-001", "device_role": "master"}

    window.load_participants()

    assert errors
    assert window.participantTable.rowCount() == 0
    window.close()


def test_participant_master_window_disables_controls_for_viewer(qt_application):
    service = StubParticipantMasterService(loaded_participants=[_participant()])
    window = ParticipantMasterWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "viewer"},
        participant_master_service=service,
    )

    assert window.participantTable.rowCount() == 0
    assert not window.participantTable.isEnabled()
    assert not window.addRowButton.isEnabled()
    assert not window.deleteRowButton.isEnabled()
    assert not window.saveButton.isEnabled()
    assert not window.csvImportButton.isEnabled()
    assert not hasattr(service, "loaded_license_id")
    window.close()
