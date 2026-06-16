import pytest

from app.models.participant import Participant
from app.services.participant_master_service import (
    ParticipantMasterDecryptionError,
    ParticipantMasterDuplicateError,
    ParticipantMasterService,
)


def _participant(
    participant_id: str,
    name: str = "Yamada Taro",
    department: str = "Sales",
    position: str = "Manager",
    display_name: str = "",
    hourly_rate: int = 6000,
) -> Participant:
    return Participant(
        participant_id=participant_id,
        is_active=True,
        name=name,
        department=department,
        position=position,
        display_name=display_name,
        hourly_rate=hourly_rate,
    )


def test_load_participants_returns_empty_list_when_file_missing(tmp_path):
    service = ParticipantMasterService(
        tmp_path / "data" / "participants.enc",
        tmp_path / "logs" / "error.log",
    )

    assert service.load_participants("LIC-TEST-001") == []


def test_save_and_load_participants_round_trip_encrypted_file(tmp_path):
    master_path = tmp_path / "data" / "participants.enc"
    service = ParticipantMasterService(master_path, tmp_path / "logs" / "error.log")
    participants = [
        _participant("P-000001", display_name="A", hourly_rate=6000),
        _participant("P-000002", name="Sato Hanako", hourly_rate=4000),
    ]

    service.save_participants(participants, "LIC-TEST-001")
    loaded_participants = service.load_participants("LIC-TEST-001")

    assert loaded_participants == participants
    encrypted_bytes = master_path.read_bytes()
    assert b"Yamada" not in encrypted_bytes
    assert b"6000" not in encrypted_bytes


def test_save_participants_rejects_exact_duplicate_identity(tmp_path):
    log_file = tmp_path / "logs" / "error.log"
    service = ParticipantMasterService(
        tmp_path / "data" / "participants.enc",
        log_file,
    )
    participants = [
        _participant("P-000001", display_name="A"),
        _participant("P-000002", display_name="A"),
    ]

    with pytest.raises(ParticipantMasterDuplicateError):
        service.save_participants(participants, "LIC-TEST-001")

    log_content = log_file.read_text(encoding="utf-8")
    assert "participant_master_save" in log_content
    assert "ParticipantMasterError" in log_content
    assert "ParticipantMasterDuplicateError" in log_content
    assert "Yamada Taro" not in log_content
    assert "6000" not in log_content


def test_save_participants_requires_display_name_for_same_base_identity(tmp_path):
    service = ParticipantMasterService(
        tmp_path / "data" / "participants.enc",
        tmp_path / "logs" / "error.log",
    )
    participants = [
        _participant("P-000001", display_name="A"),
        _participant("P-000002", display_name=""),
    ]

    with pytest.raises(ParticipantMasterDuplicateError):
        service.save_participants(participants, "LIC-TEST-001")


def test_save_participants_allows_same_base_identity_with_distinct_display_names(
    tmp_path,
):
    service = ParticipantMasterService(
        tmp_path / "data" / "participants.enc",
        tmp_path / "logs" / "error.log",
    )
    participants = [
        _participant("P-000001", display_name="A"),
        _participant("P-000002", display_name="B"),
    ]

    service.save_participants(participants, "LIC-TEST-001")

    assert service.load_participants("LIC-TEST-001") == participants


def test_load_participants_raises_decryption_error_for_wrong_license_id(tmp_path):
    service = ParticipantMasterService(
        tmp_path / "data" / "participants.enc",
        tmp_path / "logs" / "error.log",
    )
    service.save_participants([_participant("P-000001")], "LIC-TEST-001")

    with pytest.raises(ParticipantMasterDecryptionError):
        service.load_participants("LIC-TEST-002")


def test_load_participants_raises_decryption_error_for_invalid_payload(tmp_path):
    master_path = tmp_path / "data" / "participants.enc"
    master_path.parent.mkdir(parents=True)
    master_path.write_bytes(b"not encrypted data")
    service = ParticipantMasterService(master_path, tmp_path / "logs" / "error.log")

    with pytest.raises(ParticipantMasterDecryptionError):
        service.load_participants("LIC-TEST-001")
