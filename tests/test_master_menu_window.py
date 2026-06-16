import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication

from app.windows.master_menu_window import MasterMenuWindow


@pytest.fixture(scope="session")
def qt_application():
    application = QApplication.instance() or QApplication([])
    return application


class DestinationWindow:
    created = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.was_shown = False
        self.__class__.created.append(self)

    def show(self):
        self.was_shown = True


def _destination_classes():
    return {
        "participant_master": DestinationWindow,
        "role_rate_master": DestinationWindow,
        "master_import": DestinationWindow,
        "master_export": DestinationWindow,
    }


def test_master_menu_enables_all_entries_for_master(qt_application):
    window = MasterMenuWindow(
        settings={"device_role": "master"},
        destination_window_classes=_destination_classes(),
    )

    assert window.participantMasterButton.isEnabled()
    assert window.roleRateMasterButton.isEnabled()
    assert window.masterImportButton.isEnabled()
    assert window.masterExportButton.isEnabled()
    window.close()


def test_master_menu_disables_unavailable_entries_for_viewer(qt_application):
    window = MasterMenuWindow(
        settings={"device_role": "viewer"},
        destination_window_classes=_destination_classes(),
    )

    assert not window.participantMasterButton.isEnabled()
    assert window.roleRateMasterButton.isEnabled()
    assert not window.masterImportButton.isEnabled()
    assert not window.masterExportButton.isEnabled()
    window.close()


@pytest.mark.parametrize(
    ("button_name", "destination_key"),
    [
        ("participantMasterButton", "participant_master"),
        ("roleRateMasterButton", "role_rate_master"),
        ("masterImportButton", "master_import"),
        ("masterExportButton", "master_export"),
    ],
)
def test_master_menu_buttons_open_destination_windows_for_master(
    qt_application,
    button_name,
    destination_key,
):
    DestinationWindow.created = []
    window = MasterMenuWindow(
        settings={"device_role": "master"},
        destination_window_classes=_destination_classes(),
    )

    getattr(window, button_name).click()

    assert len(DestinationWindow.created) == 1
    assert DestinationWindow.created[0].was_shown
    assert window.opened_windows[-1] is DestinationWindow.created[0]
    assert destination_key in window.destination_window_classes
    if destination_key in {
        "participant_master",
        "role_rate_master",
        "master_import",
        "master_export",
    }:
        assert DestinationWindow.created[0].kwargs["settings"] == {"device_role": "master"}
    window.close()


def test_master_menu_disabled_viewer_entry_does_not_open_window(qt_application):
    DestinationWindow.created = []
    window = MasterMenuWindow(
        settings={"device_role": "viewer"},
        destination_window_classes=_destination_classes(),
    )

    window.participantMasterButton.click()

    assert DestinationWindow.created == []
    assert window.opened_windows == []
    window.close()
