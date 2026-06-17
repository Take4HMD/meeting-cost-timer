import pytest

from app.models.participant import Participant
from app.services.excel_import_service import PARTICIPANT_IMPORT_HEADERS
from app.services.participant_csv_import_service import (
    ParticipantCsvImportValidationError,
    import_participants_from_csv,
)


def _write_csv(path, headers, rows):
    lines = [",".join(headers)]
    lines.extend(",".join("" if value is None else str(value) for value in row) for row in rows)
    path.write_text("\n".join(lines), encoding="utf-8-sig")


def test_import_participants_from_csv_converts_rows_to_participant_models(tmp_path):
    csv_path = tmp_path / "participants.csv"
    _write_csv(
        csv_path,
        PARTICIPANT_IMPORT_HEADERS,
        [
            ["有効", "Yamada Taro", "Sales", "Manager", "A", 6000, 1],
            ["無効", "Sato Hanako", "", "", "", "4000", ""],
        ],
    )

    participants = import_participants_from_csv(csv_path)

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


def test_import_participants_from_csv_rejects_invalid_headers(tmp_path):
    csv_path = tmp_path / "participants.csv"
    _write_csv(csv_path, ("有効", "氏名", "概算時間単価"), [["有効", "Yamada", 6000]])

    with pytest.raises(ParticipantCsvImportValidationError):
        import_participants_from_csv(csv_path)


def test_import_participants_from_csv_rejects_invalid_required_values(tmp_path):
    csv_path = tmp_path / "participants.csv"
    _write_csv(
        csv_path,
        PARTICIPANT_IMPORT_HEADERS,
        [["対象", "Yamada Taro", "", "", "", 6000, ""]],
    )

    with pytest.raises(ParticipantCsvImportValidationError):
        import_participants_from_csv(csv_path)


def test_import_participants_from_csv_rejects_duplicate_participants(tmp_path):
    csv_path = tmp_path / "participants.csv"
    _write_csv(
        csv_path,
        PARTICIPANT_IMPORT_HEADERS,
        [
            ["有効", "Yamada Taro", "Sales", "Manager", "", 6000, ""],
            ["有効", "Yamada Taro", "Sales", "Manager", "", 7000, ""],
        ],
    )

    with pytest.raises(ParticipantCsvImportValidationError):
        import_participants_from_csv(csv_path)
