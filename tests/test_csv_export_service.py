from datetime import datetime
import csv

import pytest

from app.models.common import (
    CALCULATION_MODE_DIRECT,
    CALCULATION_MODE_DISPLAY_DATA,
    CALCULATION_MODE_PRECISE,
    CALCULATION_MODE_SIMPLE,
    UNSET_MEETING_NAME,
)
from app.models.meeting import MeetingResult
from app.services.csv_export_service import (
    CSV_HEADERS,
    CsvExportError,
    export_meeting_result_csv,
    meeting_result_to_csv_row,
)


def _meeting_result(
    meeting_name: str = "Sales Meeting",
    calculation_mode: str = CALCULATION_MODE_SIMPLE,
    meeting_cost: float = 1234.5,
) -> MeetingResult:
    return MeetingResult(
        meeting_name=meeting_name,
        calculation_mode=calculation_mode,
        start_datetime=datetime(2026, 6, 4, 10, 0, 0),
        end_datetime=datetime(2026, 6, 4, 10, 30, 0),
        actual_count_seconds=1800,
        total_hourly_rate=2469,
        meeting_cost=meeting_cost,
    )


def test_meeting_result_to_csv_row_uses_output_spec_fields_only():
    row = meeting_result_to_csv_row(_meeting_result())

    assert list(row.keys()) == CSV_HEADERS
    assert row == {
        "会議名": "Sales Meeting",
        "算出方式": "簡易モード",
        "開始日時": "2026-06-04T10:00:00",
        "終了日時": "2026-06-04T10:30:00",
        "実カウント時間": 1800,
        "合算時間単価": 2469,
        "会議コスト": 1235,
    }
    assert "participants" not in row
    assert "role_counts" not in row
    assert "hourly_rate_details" not in row


@pytest.mark.parametrize(
    ("calculation_mode", "expected_label"),
    [
        (CALCULATION_MODE_PRECISE, "精密モード"),
        (CALCULATION_MODE_SIMPLE, "簡易モード"),
        (CALCULATION_MODE_DIRECT, "直接入力"),
        (CALCULATION_MODE_DISPLAY_DATA, "表示用データ"),
    ],
)
def test_meeting_result_to_csv_row_uses_csv_calculation_mode_label(
    calculation_mode, expected_label
):
    row = meeting_result_to_csv_row(_meeting_result(calculation_mode=calculation_mode))

    assert row["算出方式"] == expected_label


def test_meeting_result_to_csv_row_uses_default_meeting_name():
    row = meeting_result_to_csv_row(_meeting_result(meeting_name=""))

    assert row["会議名"] == UNSET_MEETING_NAME


def test_meeting_result_to_csv_row_rejects_invalid_result():
    with pytest.raises(CsvExportError):
        meeting_result_to_csv_row(object())


def test_export_meeting_result_csv_writes_utf8_bom_csv_with_one_result_row(tmp_path):
    output_path = tmp_path / "meeting_result.csv"

    export_meeting_result_csv(_meeting_result(), output_path)

    raw_bytes = output_path.read_bytes()
    assert raw_bytes.startswith(b"\xef\xbb\xbf")

    rows = list(
        csv.DictReader(output_path.read_text(encoding="utf-8-sig").splitlines())
    )
    assert len(rows) == 1
    assert rows[0] == {
        "会議名": "Sales Meeting",
        "算出方式": "簡易モード",
        "開始日時": "2026-06-04T10:00:00",
        "終了日時": "2026-06-04T10:30:00",
        "実カウント時間": "1800",
        "合算時間単価": "2469",
        "会議コスト": "1235",
    }


def test_export_meeting_result_csv_rejects_invalid_result(tmp_path):
    with pytest.raises(CsvExportError):
        export_meeting_result_csv(object(), tmp_path / "meeting_result.csv")
