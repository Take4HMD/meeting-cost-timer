from __future__ import annotations

import csv
from pathlib import Path

from app.models.participant import Participant
from app.services.duplicate_service import (
    find_participant_duplicate_confirmation_groups,
    find_participant_duplicate_error_groups,
)
from app.services.excel_import_service import PARTICIPANT_IMPORT_HEADERS


ACTIVE_LABEL = "有効"
INACTIVE_LABEL = "無効"


class ParticipantCsvImportError(Exception):
    pass


class ParticipantCsvImportValidationError(ParticipantCsvImportError):
    pass


def import_participants_from_csv(file_path: Path) -> list[Participant]:
    with file_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if tuple(reader.fieldnames or ()) != PARTICIPANT_IMPORT_HEADERS:
            raise ParticipantCsvImportValidationError("csv headers are invalid")

        participants = []
        for row_index, row in enumerate(reader, start=1):
            if _is_blank_row(row):
                continue
            participants.append(
                Participant(
                    participant_id=f"P-{row_index:06d}",
                    is_active=_parse_active(row["有効"], "有効"),
                    name=_required_text(row["氏名"], "氏名"),
                    department=_optional_text(row["部署"]),
                    position=_optional_text(row["役職"]),
                    display_name=_optional_text(row["識別名"]),
                    hourly_rate=_positive_int(row["概算時間単価"], "概算時間単価"),
                    sort_order=_optional_positive_int(row["表示順"], "表示順"),
                )
            )

    _validate_participant_duplicates(participants)
    return participants


def _validate_participant_duplicates(participants: list[Participant]) -> None:
    if find_participant_duplicate_error_groups(participants):
        raise ParticipantCsvImportValidationError("participant identity is duplicated")

    for group in find_participant_duplicate_confirmation_groups(participants):
        if any(not item.display_name.strip() for item in group.items):
            raise ParticipantCsvImportValidationError(
                "display_name is required for participants with same name, department, and position"
            )


def _parse_active(value: str | None, field_name: str) -> bool:
    text = _required_text(value, field_name)
    if text == ACTIVE_LABEL:
        return True
    if text == INACTIVE_LABEL:
        return False
    raise ParticipantCsvImportValidationError(f"{field_name} must be 有効 or 無効")


def _required_text(value: str | None, field_name: str) -> str:
    text = _optional_text(value)
    if not text:
        raise ParticipantCsvImportValidationError(f"{field_name} is required")
    return text


def _optional_text(value: str | None) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _positive_int(value: str | None, field_name: str) -> int:
    text = _required_text(value, field_name)
    if not text.isdecimal():
        raise ParticipantCsvImportValidationError(f"{field_name} must be an integer")
    parsed_value = int(text)
    if parsed_value < 1:
        raise ParticipantCsvImportValidationError(f"{field_name} must be at least 1")
    return parsed_value


def _optional_positive_int(value: str | None, field_name: str) -> int | None:
    text = _optional_text(value)
    if not text:
        return None
    return _positive_int(text, field_name)


def _is_blank_row(row: dict[str, str | None]) -> bool:
    return all(_optional_text(row.get(header)) == "" for header in PARTICIPANT_IMPORT_HEADERS)
