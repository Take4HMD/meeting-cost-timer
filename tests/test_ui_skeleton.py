import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication

from app.utils.ui_loader import ui_path
from app.windows.base_window import (
    UI_MINIMUM_SIZES,
    WINDOW_CONTENT_MARGINS,
    WINDOW_LAYOUT_SPACING,
)
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


@pytest.mark.parametrize(("window_class", "file_name", "_object_names"), WINDOW_CASES)
def test_window_has_readable_minimum_size(
    qt_application,
    window_class,
    file_name,
    _object_names,
):
    window = window_class()
    minimum_width, minimum_height = UI_MINIMUM_SIZES[file_name]

    assert window.minimumWidth() >= minimum_width
    assert window.minimumHeight() >= minimum_height
    assert window.width() >= minimum_width
    assert window.height() >= minimum_height

    window.close()


@pytest.mark.parametrize(("window_class", "_file_name", "_object_names"), WINDOW_CASES)
def test_window_has_readable_layout_spacing(
    qt_application,
    window_class,
    _file_name,
    _object_names,
):
    window = window_class()
    root_layout = window.centralWidget().layout()
    margins = root_layout.contentsMargins()

    assert (
        margins.left(),
        margins.top(),
        margins.right(),
        margins.bottom(),
    ) == WINDOW_CONTENT_MARGINS
    assert root_layout.spacing() >= WINDOW_LAYOUT_SPACING
    assert _minimum_nested_layout_spacing(root_layout) >= WINDOW_LAYOUT_SPACING

    window.close()


def _minimum_nested_layout_spacing(layout):
    spacings = [layout.spacing()]
    for index in range(layout.count()):
        child_layout = layout.itemAt(index).layout()
        if child_layout is not None:
            spacings.append(_minimum_nested_layout_spacing(child_layout))
    return min(spacings)
