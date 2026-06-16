import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication, QTableWidgetItem

from app.models.common import CALCULATION_MODE_SIMPLE
from app.models.role_rate import RoleRate
from app.windows.meeting_start_settings_window import MeetingStartSettingsWindow
from app.windows.simple_role_count_window import SimpleRoleCountWindow


@pytest.fixture(scope="session")
def qt_application():
    application = QApplication.instance() or QApplication([])
    return application


class StubRoleRateMasterService:
    def __init__(self, loaded_role_rates=None, load_error=None):
        self.loaded_role_rates = loaded_role_rates or []
        self.load_error = load_error
        self.loaded_license_id = None

    def load_role_rates(self, license_id):
        if self.load_error is not None:
            raise self.load_error
        self.loaded_license_id = license_id
        return self.loaded_role_rates


def _role_rate(
    role_rate_id="R-000001",
    is_active=True,
    role_name="Manager",
    hourly_rate=6000,
    sort_order=1,
):
    return RoleRate(
        role_rate_id=role_rate_id,
        is_active=is_active,
        role_name=role_name,
        hourly_rate=hourly_rate,
        sort_order=sort_order,
    )


def test_simple_role_count_window_loads_active_role_rates(qt_application):
    service = StubRoleRateMasterService(
        loaded_role_rates=[
            _role_rate(role_name="Manager", hourly_rate=6000),
            _role_rate(
                role_rate_id="R-000002",
                is_active=False,
                role_name="Inactive",
                hourly_rate=3000,
            ),
            _role_rate(
                role_rate_id="R-000003",
                role_name="Staff",
                hourly_rate=4000,
            ),
        ]
    )

    window = SimpleRoleCountWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "viewer"},
        role_rate_master_service=service,
    )

    assert service.loaded_license_id == "LIC-TEST-001"
    assert window.roleCountTable.rowCount() == 2
    assert window.roleCountTable.item(0, 0).text() == "Manager"
    assert window.roleCountTable.item(0, 1).text() == "0"
    assert window.roleCountTable.item(1, 0).text() == "Staff"
    assert window.roleCountTable.item(1, 1).text() == "0"
    window.close()


def test_simple_role_count_window_calculates_total_hourly_rate(qt_application):
    confirmed_values = []
    service = StubRoleRateMasterService(
        loaded_role_rates=[
            _role_rate(role_name="Manager", hourly_rate=6000),
            _role_rate(role_rate_id="R-000002", role_name="Staff", hourly_rate=4000),
        ]
    )
    window = SimpleRoleCountWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "master"},
        role_rate_master_service=service,
        on_confirm=confirmed_values.append,
    )
    window.roleCountTable.setItem(0, 1, QTableWidgetItem("2"))
    window.roleCountTable.setItem(1, 1, QTableWidgetItem("3"))

    result = window.confirm_input()

    assert result == 24000
    assert confirmed_values == [24000]
    window.close()


def test_simple_role_count_window_clear_counts(qt_application):
    service = StubRoleRateMasterService(
        loaded_role_rates=[_role_rate(), _role_rate(role_rate_id="R-000002")]
    )
    window = SimpleRoleCountWindow(
        settings={"license_id": "LIC-TEST-001"},
        role_rate_master_service=service,
    )
    window.roleCountTable.setItem(0, 1, QTableWidgetItem("2"))
    window.roleCountTable.setItem(1, 1, QTableWidgetItem("3"))

    window.clear_counts()

    assert window.roleCountTable.item(0, 1).text() == "0"
    assert window.roleCountTable.item(1, 1).text() == "0"
    window.close()


@pytest.mark.parametrize("count_text", ["", "-1", "1.5", "abc"])
def test_simple_role_count_window_shows_error_for_invalid_count(
    qt_application,
    count_text,
):
    errors = []
    service = StubRoleRateMasterService(loaded_role_rates=[_role_rate()])
    window = SimpleRoleCountWindow(
        settings={"license_id": "LIC-TEST-001"},
        role_rate_master_service=service,
        on_confirm=lambda total_hourly_rate: None,
    )
    window._show_error = lambda title, message: errors.append((title, message))
    window.roleCountTable.setItem(0, 1, QTableWidgetItem(count_text))

    result = window.confirm_input()

    assert result is None
    assert errors
    window.close()


def test_simple_role_count_window_shows_error_when_total_people_is_zero(
    qt_application,
):
    errors = []
    service = StubRoleRateMasterService(loaded_role_rates=[_role_rate()])
    window = SimpleRoleCountWindow(
        settings={"license_id": "LIC-TEST-001"},
        role_rate_master_service=service,
    )
    window._show_error = lambda title, message: errors.append((title, message))

    result = window.confirm_input()

    assert result is None
    assert errors
    window.close()


def test_simple_role_count_window_handles_load_error(qt_application, monkeypatch):
    errors = []
    monkeypatch.setattr(
        SimpleRoleCountWindow,
        "_show_error",
        lambda self, title, message: errors.append((title, message)),
    )
    window = SimpleRoleCountWindow(
        settings={"license_id": "LIC-TEST-001"},
        role_rate_master_service=StubRoleRateMasterService(load_error=RuntimeError()),
    )

    window.load_role_rates()

    assert errors
    assert window.roleCountTable.rowCount() == 0
    window.close()


def test_simple_role_count_window_reflects_value_to_meeting_start_settings_window(
    qt_application,
):
    service = StubRoleRateMasterService(
        loaded_role_rates=[_role_rate(role_name="Manager", hourly_rate=6000)]
    )
    parent_window = MeetingStartSettingsWindow(
        settings={"license_id": "LIC-TEST-001", "device_role": "viewer"},
        destination_window_classes={
            "precise": SimpleRoleCountWindow,
            "simple": SimpleRoleCountWindow,
            "display_data": SimpleRoleCountWindow,
            "direct": SimpleRoleCountWindow,
            "count_display": SimpleRoleCountWindow,
        },
    )

    simple_window = SimpleRoleCountWindow(
        settings=parent_window.settings,
        role_rate_master_service=service,
        on_confirm=parent_window.apply_simple_input,
    )
    simple_window.roleCountTable.setItem(0, 1, QTableWidgetItem("2"))

    result = simple_window.confirm_input()

    assert result == 12000
    assert parent_window.totalHourlyRateSpinBox.value() == 12000
    assert parent_window.calculationModeComboBox.currentData() == CALCULATION_MODE_SIMPLE
    simple_window.close()
    parent_window.close()
