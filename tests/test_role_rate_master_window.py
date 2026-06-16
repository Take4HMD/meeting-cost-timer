import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication, QTableWidgetItem

from app.models.role_rate import RoleRate
from app.windows.role_rate_master_window import RoleRateMasterWindow


@pytest.fixture(scope="session")
def qt_application():
    application = QApplication.instance() or QApplication([])
    return application


class StubRoleRateMasterService:
    def __init__(self, loaded_role_rates=None, load_error=None, save_error=None):
        self.loaded_role_rates = loaded_role_rates or []
        self.load_error = load_error
        self.save_error = save_error
        self.saved_role_rates = None
        self.saved_license_id = None

    def load_role_rates(self, license_id):
        if self.load_error is not None:
            raise self.load_error
        self.loaded_license_id = license_id
        return self.loaded_role_rates

    def save_role_rates(self, role_rates, license_id):
        if self.save_error is not None:
            raise self.save_error
        self.saved_role_rates = role_rates
        self.saved_license_id = license_id


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


def test_role_rate_master_window_loads_role_rates_into_table(qt_application):
    service = StubRoleRateMasterService(
        loaded_role_rates=[
            _role_rate(),
            _role_rate(
                role_rate_id="R-000002",
                is_active=False,
                role_name="Staff",
                hourly_rate=3000,
                sort_order=None,
            ),
        ]
    )

    window = RoleRateMasterWindow(
        settings={"license_id": "LIC-TEST-001"},
        role_rate_master_service=service,
    )

    assert service.loaded_license_id == "LIC-TEST-001"
    assert window.roleRateTable.rowCount() == 2
    assert window.roleRateTable.item(0, 0).text() == "有効"
    assert window.roleRateTable.item(0, 1).text() == "Manager"
    assert window.roleRateTable.item(0, 2).text() == "6000"
    assert window.roleRateTable.item(0, 3).text() == "1"
    assert window.roleRateTable.item(1, 0).text() == "無効"
    assert window.roleRateTable.item(1, 3).text() == ""
    window.close()


def test_role_rate_master_window_adds_and_deletes_rows(qt_application):
    window = RoleRateMasterWindow(
        settings={"license_id": "LIC-TEST-001"},
        role_rate_master_service=StubRoleRateMasterService(),
    )

    window.addRowButton.click()
    assert window.roleRateTable.rowCount() == 1
    assert window.roleRateTable.item(0, 0).text() == "有効"
    assert window.roleRateTable.item(0, 1).text() == ""

    window.roleRateTable.selectRow(0)
    window.deleteRowButton.click()

    assert window.roleRateTable.rowCount() == 0
    window.close()


def test_role_rate_master_window_saves_table_values(qt_application):
    service = StubRoleRateMasterService(loaded_role_rates=[_role_rate()])
    window = RoleRateMasterWindow(
        settings={"license_id": "LIC-TEST-001"},
        role_rate_master_service=service,
    )

    window.roleRateTable.setItem(0, 1, QTableWidgetItem("Director"))
    window.roleRateTable.setItem(0, 2, QTableWidgetItem("8000"))
    window.roleRateTable.setItem(0, 3, QTableWidgetItem(""))
    window._show_error = pytest.fail

    window.saveButton.click()

    assert service.saved_license_id == "LIC-TEST-001"
    assert service.saved_role_rates == [
        RoleRate(
            role_rate_id="R-000001",
            is_active=True,
            role_name="Director",
            hourly_rate=8000,
            sort_order=None,
        )
    ]
    window.close()


def test_role_rate_master_window_shows_error_when_save_validation_fails(qt_application):
    service = StubRoleRateMasterService(loaded_role_rates=[_role_rate()])
    errors = []
    window = RoleRateMasterWindow(
        settings={"license_id": "LIC-TEST-001"},
        role_rate_master_service=service,
    )
    window._show_error = lambda title, message: errors.append((title, message))

    window.roleRateTable.setItem(0, 2, QTableWidgetItem("0"))
    window.saveButton.click()

    assert errors
    assert service.saved_role_rates is None
    window.close()


def test_role_rate_master_window_handles_load_error(qt_application):
    errors = []
    window = RoleRateMasterWindow(
        settings={},
        role_rate_master_service=StubRoleRateMasterService(load_error=RuntimeError()),
    )
    window._show_error = lambda title, message: errors.append((title, message))
    window.settings = {"license_id": "LIC-TEST-001"}

    window.load_role_rates()

    assert errors
    assert window.roleRateTable.rowCount() == 0
    window.close()
