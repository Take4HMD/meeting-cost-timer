import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication

from app.utils.ui_loader import ui_path
from app.windows import (
    CountDisplayWindow,
    DirectInputWindow,
    DisplaySettingsWindow,
    LicenseSettingsWindow,
    MainMenuWindow,
    MasterExportWindow,
    MasterImportWindow,
    MasterMenuWindow,
    McdImportWindow,
    MeetingStartSettingsWindow,
    ParticipantMasterWindow,
    PreciseParticipantSelectionWindow,
    ResultExportWindow,
    RoleRateMasterWindow,
    SimpleRoleCountWindow,
)


WINDOW_CASES = [
    (MainMenuWindow, "main_menu.ui", ("startMeetingButton", "exitButton")),
    (LicenseSettingsWindow, "license_settings.ui", ("licenseIdLineEdit",)),
    (MasterMenuWindow, "master_menu.ui", ("participantMasterButton",)),
    (ParticipantMasterWindow, "participant_master.ui", ("participantTable",)),
    (RoleRateMasterWindow, "role_rate_master.ui", ("roleRateTable",)),
    (MasterImportWindow, "master_import.ui", ("importTargetComboBox",)),
    (MasterExportWindow, "master_export.ui", ("exportTargetComboBox",)),
    (
        MeetingStartSettingsWindow,
        "meeting_start_settings.ui",
        ("meetingNameLineEdit", "calculationModeComboBox"),
    ),
    (
        PreciseParticipantSelectionWindow,
        "precise_participant_selection.ui",
        ("participantSelectionTable",),
    ),
    (SimpleRoleCountWindow, "simple_role_count.ui", ("roleCountTable",)),
    (McdImportWindow, "mcd_import.ui", ("mcdFileLineEdit",)),
    (DirectInputWindow, "direct_input.ui", ("totalHourlyRateLineEdit",)),
    (CountDisplayWindow, "count_display.ui", ("costLabel",)),
    (ResultExportWindow, "result_export.ui", ("outputFormatComboBox",)),
    (DisplaySettingsWindow, "display_settings.ui", ("displayModeComboBox",)),
]


@pytest.fixture(scope="session")
def qt_application():
    application = QApplication.instance() or QApplication([])
    return application


@pytest.mark.parametrize(("window_class", "file_name", "_object_names"), WINDOW_CASES)
def test_ui_file_exists_for_each_window(window_class, file_name, _object_names):
    assert window_class.ui_file_name == file_name
    assert ui_path(file_name).exists()


@pytest.mark.parametrize(("window_class", "_file_name", "object_names"), WINDOW_CASES)
def test_window_loads_ui_and_exposes_defined_objects(
    qt_application,
    window_class,
    _file_name,
    object_names,
):
    window = window_class()

    for object_name in object_names:
        assert hasattr(window, object_name)

    window.close()
