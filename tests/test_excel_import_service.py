import pytest
from openpyxl import Workbook

from app.models.participant import Participant
from app.models.role_rate import RoleRate
from app.services.excel_import_service import (
    PARTICIPANT_IMPORT_HEADERS,
    ROLE_RATE_IMPORT_HEADERS,
    ExcelImportPermissionError,
    ExcelImportValidationError,
    import_participants_from_excel,
    import_role_rates_from_excel,
)


def _write_workbook(path, headers, rows):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(list(headers))
    for row in rows:
        worksheet.append(row)
    workbook.save(path)
    workbook.close()


def test_import_participants_from_excel_converts_rows_to_participant_models(tmp_path):
    excel_path = tmp_path / "participants.xlsx"
    _write_workbook(
        excel_path,
        PARTICIPANT_IMPORT_HEADERS,
        [
            ["有効", "Yamada Taro", "Sales", "Manager", "A", 6000, 1],
            ["無効", "Sato Hanako", None, None, None, "4000", None],
        ],
    )

    participants = import_participants_from_excel(excel_path, "master")

    assert participants == [
        Participant(
            participant_id="P-000001",
            is_active=True,
            name="Yamada Taro",
            department="Sales",
            position="Manager",
            display_name="A",
            hourly_rate=6000,
            sort_order=1,
        ),
        Participant(
            participant_id="P-000002",
            is_active=False,
            name="Sato Hanako",
            hourly_rate=4000,
        ),
    ]


def test_import_participants_from_excel_rejects_viewer_device(tmp_path):
    excel_path = tmp_path / "participants.xlsx"
    _write_workbook(excel_path, PARTICIPANT_IMPORT_HEADERS, [])

    with pytest.raises(ExcelImportPermissionError):
        import_participants_from_excel(excel_path, "viewer")


def test_import_participants_from_excel_rejects_invalid_headers(tmp_path):
    excel_path = tmp_path / "participants.xlsx"
    _write_workbook(
        excel_path,
        ("有効", "氏名", "概算時間単価"),
        [["有効", "Yamada Taro", 6000]],
    )

    with pytest.raises(ExcelImportValidationError):
        import_participants_from_excel(excel_path, "master")


def test_import_participants_from_excel_rejects_invalid_required_values(tmp_path):
    excel_path = tmp_path / "participants.xlsx"
    _write_workbook(
        excel_path,
        PARTICIPANT_IMPORT_HEADERS,
        [["対象", "Yamada Taro", "", "", "", 6000, None]],
    )

    with pytest.raises(ExcelImportValidationError):
        import_participants_from_excel(excel_path, "master")


def test_import_participants_from_excel_rejects_duplicate_participants(tmp_path):
    excel_path = tmp_path / "participants.xlsx"
    _write_workbook(
        excel_path,
        PARTICIPANT_IMPORT_HEADERS,
        [
            ["有効", "Yamada Taro", "Sales", "Manager", "", 6000, None],
            ["有効", "Yamada Taro", "Sales", "Manager", "", 7000, None],
        ],
    )

    with pytest.raises(ExcelImportValidationError):
        import_participants_from_excel(excel_path, "master")


def test_import_role_rates_from_excel_converts_rows_to_role_rate_models(tmp_path):
    excel_path = tmp_path / "role_rates.xlsx"
    _write_workbook(
        excel_path,
        ROLE_RATE_IMPORT_HEADERS,
        [
            ["有効", "Manager", 6000, 1],
            ["無効", "Staff", "3000", None],
        ],
    )

    role_rates = import_role_rates_from_excel(excel_path, "master")

    assert role_rates == [
        RoleRate(
            role_rate_id="R-000001",
            is_active=True,
            role_name="Manager",
            hourly_rate=6000,
            sort_order=1,
        ),
        RoleRate(
            role_rate_id="R-000002",
            is_active=False,
            role_name="Staff",
            hourly_rate=3000,
        ),
    ]


def test_import_role_rates_from_excel_rejects_viewer_device(tmp_path):
    excel_path = tmp_path / "role_rates.xlsx"
    _write_workbook(excel_path, ROLE_RATE_IMPORT_HEADERS, [])

    with pytest.raises(ExcelImportPermissionError):
        import_role_rates_from_excel(excel_path, "viewer")


def test_import_role_rates_from_excel_rejects_invalid_hourly_rate(tmp_path):
    excel_path = tmp_path / "role_rates.xlsx"
    _write_workbook(
        excel_path,
        ROLE_RATE_IMPORT_HEADERS,
        [["有効", "Manager", 0, None]],
    )

    with pytest.raises(ExcelImportValidationError):
        import_role_rates_from_excel(excel_path, "master")


def test_import_role_rates_from_excel_rejects_duplicate_role_name(tmp_path):
    excel_path = tmp_path / "role_rates.xlsx"
    _write_workbook(
        excel_path,
        ROLE_RATE_IMPORT_HEADERS,
        [
            ["有効", "Manager", 6000, None],
            ["有効", " Manager ", 7000, None],
        ],
    )

    with pytest.raises(ExcelImportValidationError):
        import_role_rates_from_excel(excel_path, "master")
