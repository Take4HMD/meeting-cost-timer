import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from app.models.common import CALCULATION_MODE_PRECISE
from app.models.participant import Participant
from app.windows.meeting_start_settings_window import MeetingStartSettingsWindow
from app.windows.precise_participant_selection_window import (
    PreciseParticipantSelectionWindow,
)


@pytest.fixture(scope="session")
def qt_application():
    application = QApplication.instance() or QApplication([])
    return application


class StubParticipantMasterService:
    def __init__(self, loaded_participants=None, load_error=None):
        self.loaded_participants = loaded_participants or []
        self.load_error = load_error
        self.loaded_license_id = None

    def load_participants(self, license_id):
        if self.load_error is not None:
            raise self.load_error
        self.loaded_license_id = license_id
        return self.loaded_participants


def _participant(
    participant_id="P-000001",
    is_active=True,
    name="Sato Taro",
    department="Sales",
    position="Manager",
    display_name="Taro",
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


def test_precise_participant_selection_window_loads_active_participants_only(
    qt_application,
):
    service = StubParticipantMasterService(
        loaded_participants=[
            _participant(name="Sato Taro", hourly_rate=6000),
            _participant(
                participant_id="P-000002",
                is_active=False,
                name="Inactive User",
                hourly_rate=3000,
            ),
            _participant(
                participant_id="P-000003",
                name="Suzuki Jiro",
                department="Dev",
                position="Staff",
                display_name="Jiro",
                hourly_rate=4000,
            ),
        ]
    )

    window = PreciseParticipantSelectionWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "master"},
        participant_master_service=service,
    )

    assert service.loaded_license_id == "LIC-TEST-001"
    assert window.participantSelectionTable.rowCount() == 2
    assert window.participantSelectionTable.item(0, 1).text() == "Sato Taro"
    assert window.participantSelectionTable.item(1, 1).text() == "Suzuki Jiro"
    window.close()


def test_precise_participant_selection_window_does_not_display_hourly_rate(
    qt_application,
):
    service = StubParticipantMasterService(
        loaded_participants=[_participant(hourly_rate=987654)]
    )
    window = PreciseParticipantSelectionWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "master"},
        participant_master_service=service,
    )

    visible_texts = [
        window.participantSelectionTable.item(row, column).text()
        for row in range(window.participantSelectionTable.rowCount())
        for column in range(window.participantSelectionTable.columnCount())
        if window.participantSelectionTable.item(row, column) is not None
    ]

    assert "987654" not in visible_texts
    window.close()


def test_precise_participant_selection_window_calculates_selected_participants(
    qt_application,
):
    confirmed_values = []
    service = StubParticipantMasterService(
        loaded_participants=[
            _participant(name="Sato Taro", hourly_rate=6000),
            _participant(
                participant_id="P-000002",
                name="Suzuki Jiro",
                hourly_rate=4000,
            ),
        ]
    )
    window = PreciseParticipantSelectionWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "master"},
        participant_master_service=service,
        on_confirm=confirmed_values.append,
    )
    window.participantSelectionTable.item(0, 0).setCheckState(Qt.CheckState.Checked)
    window.participantSelectionTable.item(1, 0).setCheckState(Qt.CheckState.Checked)

    result = window.confirm_selection()

    assert result == 10000
    assert confirmed_values == [10000]
    window.close()


def test_precise_participant_selection_window_clear_selection(qt_application):
    service = StubParticipantMasterService(loaded_participants=[_participant()])
    window = PreciseParticipantSelectionWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "master"},
        participant_master_service=service,
    )
    window.participantSelectionTable.item(0, 0).setCheckState(Qt.CheckState.Checked)

    window.clear_selection()

    assert window.participantSelectionTable.item(0, 0).checkState() == (
        Qt.CheckState.Unchecked
    )
    window.close()


def test_precise_participant_selection_window_shows_error_when_not_selected(
    qt_application,
):
    errors = []
    service = StubParticipantMasterService(loaded_participants=[_participant()])
    window = PreciseParticipantSelectionWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "master"},
        participant_master_service=service,
    )
    window._show_error = lambda title, message: errors.append((title, message))

    result = window.confirm_selection()

    assert result is None
    assert errors
    window.close()


def test_precise_participant_selection_window_is_disabled_for_viewer(qt_application):
    service = StubParticipantMasterService(loaded_participants=[_participant()])
    errors = []
    window = PreciseParticipantSelectionWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "viewer"},
        participant_master_service=service,
    )
    window._show_error = lambda title, message: errors.append((title, message))

    result = window.confirm_selection()

    assert result is None
    assert errors
    assert not window.participantSelectionTable.isEnabled()
    assert not window.confirmButton.isEnabled()
    assert window.participantSelectionTable.rowCount() == 0
    window.close()


def test_precise_participant_selection_window_handles_load_error(
    qt_application,
    monkeypatch,
):
    errors = []
    monkeypatch.setattr(
        PreciseParticipantSelectionWindow,
        "_show_error",
        lambda self, title, message: errors.append((title, message)),
    )
    window = PreciseParticipantSelectionWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "master"},
        participant_master_service=StubParticipantMasterService(
            load_error=RuntimeError()
        ),
    )

    window.load_participants()

    assert errors
    assert window.participantSelectionTable.rowCount() == 0
    window.close()


def test_precise_participant_selection_window_reflects_value_to_meeting_start_settings_window(
    qt_application,
):
    service = StubParticipantMasterService(
        loaded_participants=[_participant(hourly_rate=6000)]
    )
    parent_window = MeetingStartSettingsWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "master"},
    )
    precise_window = PreciseParticipantSelectionWindow(
        settings=parent_window.settings,
        participant_master_service=service,
        on_confirm=parent_window.apply_precise_input,
    )
    precise_window.participantSelectionTable.item(0, 0).setCheckState(
        Qt.CheckState.Checked
    )

    result = precise_window.confirm_selection()

    assert result == 6000
    assert parent_window.totalHourlyRateSpinBox.value() == 6000
    assert parent_window.calculationModeComboBox.currentData() == CALCULATION_MODE_PRECISE
    precise_window.close()
    parent_window.close()
