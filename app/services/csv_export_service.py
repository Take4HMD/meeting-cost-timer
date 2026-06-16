from __future__ import annotations

import csv
from pathlib import Path

from app.models.common import (
    CALCULATION_MODE_DIRECT,
    CALCULATION_MODE_DISPLAY_DATA,
    CALCULATION_MODE_PRECISE,
    CALCULATION_MODE_SIMPLE,
)
from app.models.meeting import MeetingResult
from app.services.calculation_service import round_meeting_cost_for_output
from app.utils.logging_config import configure_error_logging, log_exception


CSV_HEADERS = [
    "会議名",
    "算出方式",
    "開始日時",
    "終了日時",
    "実カウント時間",
    "合算時間単価",
    "会議コスト",
]

CSV_CALCULATION_MODE_LABELS = {
    CALCULATION_MODE_PRECISE: "精密モード",
    CALCULATION_MODE_SIMPLE: "簡易モード",
    CALCULATION_MODE_DIRECT: "直接入力",
    CALCULATION_MODE_DISPLAY_DATA: "表示用データ",
}


class CsvExportError(Exception):
    pass


def export_meeting_result_csv(result: MeetingResult, output_path: Path) -> None:
    if not isinstance(result, MeetingResult):
        raise CsvExportError("result must be MeetingResult")

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerow(meeting_result_to_csv_row(result))
    except OSError as exc:
        logger = configure_error_logging()
        log_exception("csv_export", exc, output_path, logger)
        raise


def meeting_result_to_csv_row(result: MeetingResult) -> dict[str, str | int]:
    if not isinstance(result, MeetingResult):
        raise CsvExportError("result must be MeetingResult")

    return {
        "会議名": result.display_meeting_name,
        "算出方式": _calculation_mode_label(result.calculation_mode),
        "開始日時": result.start_datetime.isoformat(),
        "終了日時": result.end_datetime.isoformat(),
        "実カウント時間": result.actual_count_seconds,
        "合算時間単価": result.total_hourly_rate,
        "会議コスト": round_meeting_cost_for_output(result.meeting_cost),
    }


def _calculation_mode_label(calculation_mode: str) -> str:
    return CSV_CALCULATION_MODE_LABELS[calculation_mode]
