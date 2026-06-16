from __future__ import annotations

from pathlib import Path
from typing import Iterable

from openpyxl import Workbook

from app.models.participant import Participant
from app.models.role_rate import RoleRate
from app.services.excel_import_service import (
    PARTICIPANT_IMPORT_HEADERS,
    ROLE_RATE_IMPORT_HEADERS,
    ACTIVE_LABEL,
    INACTIVE_LABEL,
)


PARTICIPANT_MASTER_EXPORT_FILE_NAME = "participant_master_export.xlsx"
ROLE_RATE_MASTER_EXPORT_FILE_NAME = "role_rate_master_export.xlsx"


def export_participants_to_excel(
    participants: Iterable[Participant],
    output_path: Path,
) -> None:
    rows = [
        [
            ACTIVE_LABEL if participant.is_active else INACTIVE_LABEL,
            participant.name,
            participant.department,
            participant.position,
            participant.display_name,
            participant.hourly_rate,
            participant.sort_order,
        ]
        for participant in participants
    ]
    _write_workbook(PARTICIPANT_IMPORT_HEADERS, rows, output_path)


def export_role_rates_to_excel(
    role_rates: Iterable[RoleRate],
    output_path: Path,
) -> None:
    rows = [
        [
            ACTIVE_LABEL if role_rate.is_active else INACTIVE_LABEL,
            role_rate.role_name,
            role_rate.hourly_rate,
            role_rate.sort_order,
        ]
        for role_rate in role_rates
    ]
    _write_workbook(ROLE_RATE_IMPORT_HEADERS, rows, output_path)


def _write_workbook(
    headers: tuple[str, ...],
    rows: list[list],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    try:
        worksheet = workbook.active
        worksheet.append(list(headers))
        for row in rows:
            worksheet.append(row)
        workbook.save(output_path)
    finally:
        workbook.close()
