from __future__ import annotations

import json
from pathlib import Path
import re

from app.models.participant import Participant
from app.services.duplicate_service import (
    find_participant_duplicate_confirmation_groups,
    find_participant_duplicate_error_groups,
)
from app.utils.crypto import DecryptionError, decrypt_text, encrypt_text
from app.utils.logging_config import configure_error_logging, log_exception
from app.utils.paths import project_path


PARTICIPANT_MASTER_SCHEMA_VERSION = 1
PARTICIPANT_MASTER_RELATIVE_PATH = ("data", "participants.enc")


class ParticipantMasterError(Exception):
    pass


class ParticipantMasterDecryptionError(ParticipantMasterError):
    pass


class ParticipantMasterDuplicateError(ParticipantMasterError):
    pass


class ParticipantMasterValidationError(ParticipantMasterError):
    pass


class ParticipantMasterService:
    def __init__(
        self,
        master_path: Path | None = None,
        log_file: Path | None = None,
    ) -> None:
        self.master_path = master_path or project_path(*PARTICIPANT_MASTER_RELATIVE_PATH)
        self.logger = configure_error_logging(log_file)

    def save_participants(
        self,
        participants: list[Participant],
        license_id: str,
    ) -> None:
        try:
            self._validate_participants_for_save(participants)
            payload = json.dumps(
                self._to_payload(participants),
                ensure_ascii=False,
                separators=(",", ":"),
            )
            encrypted_payload = encrypt_text(payload, license_id)

            self.master_path.parent.mkdir(parents=True, exist_ok=True)
            self.master_path.write_bytes(encrypted_payload)
        except Exception as exc:
            log_exception(
                "participant_master_save",
                ParticipantMasterError(type(exc).__name__),
                self.master_path,
                self.logger,
            )
            raise

    def load_participants(self, license_id: str) -> list[Participant]:
        if not self.master_path.exists():
            return []

        encrypted_payload = self.master_path.read_bytes()
        try:
            payload_text = decrypt_text(encrypted_payload, license_id)
        except DecryptionError as exc:
            log_exception("participant_master_decrypt", exc, self.master_path, self.logger)
            raise ParticipantMasterDecryptionError(
                "participant master could not be decrypted"
            ) from exc

        try:
            payload = json.loads(payload_text)
            return self._participants_from_payload(payload)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            log_exception("participant_master_load", exc, self.master_path, self.logger)
            raise ParticipantMasterValidationError(
                "participant master format is invalid"
            ) from exc

    def _validate_participants_for_save(self, participants: list[Participant]) -> None:
        if not isinstance(participants, list):
            raise ParticipantMasterValidationError("participants must be a list")
        if not all(isinstance(participant, Participant) for participant in participants):
            raise ParticipantMasterValidationError("participants must contain Participant")

        duplicate_error_groups = find_participant_duplicate_error_groups(participants)
        if duplicate_error_groups:
            raise ParticipantMasterDuplicateError("participant identity is duplicated")

        duplicate_confirmation_groups = (
            find_participant_duplicate_confirmation_groups(participants)
        )
        for group in duplicate_confirmation_groups:
            if any(not item.display_name.strip() for item in group.items):
                raise ParticipantMasterDuplicateError(
                    "display_name is required for participants with same name, department, and position"
                )

    def _to_payload(self, participants: list[Participant]) -> dict:
        return {
            "schema_version": PARTICIPANT_MASTER_SCHEMA_VERSION,
            "last_participant_no": _last_participant_no(participants),
            "participants": [
                {
                    "participant_id": participant.participant_id,
                    "is_active": participant.is_active,
                    "name": participant.name,
                    "department": participant.department,
                    "position": participant.position,
                    "display_name": participant.display_name,
                    "hourly_rate": participant.hourly_rate,
                    "sort_order": participant.sort_order,
                }
                for participant in participants
            ],
        }

    def _participants_from_payload(self, payload: dict) -> list[Participant]:
        if not isinstance(payload, dict):
            raise ValueError("participant master payload must be an object")
        if payload.get("schema_version") != PARTICIPANT_MASTER_SCHEMA_VERSION:
            raise ValueError("unsupported participant master schema_version")

        participants = payload.get("participants")
        if not isinstance(participants, list):
            raise ValueError("participants must be a list")

        loaded_participants = []
        for item in participants:
            if not isinstance(item, dict):
                raise ValueError("participant item must be an object")
            loaded_participants.append(
                Participant(
                    participant_id=item["participant_id"],
                    is_active=item["is_active"],
                    name=item["name"],
                    department=item.get("department", ""),
                    position=item.get("position", ""),
                    display_name=item.get("display_name", ""),
                    hourly_rate=item["hourly_rate"],
                    sort_order=item.get("sort_order"),
                )
            )
        return loaded_participants


def _last_participant_no(participants: list[Participant]) -> int:
    last_no = 0
    for participant in participants:
        match = re.fullmatch(r"P-(\d{6})", participant.participant_id)
        if match:
            last_no = max(last_no, int(match.group(1)))
    return last_no
