from __future__ import annotations

import json
from pathlib import Path
import re

from app.models.role_rate import RoleRate
from app.services.duplicate_service import find_role_rate_duplicate_groups
from app.utils.crypto import DecryptionError, decrypt_text, encrypt_text
from app.utils.logging_config import configure_error_logging, log_exception
from app.utils.paths import project_path


ROLE_RATE_MASTER_SCHEMA_VERSION = 1
ROLE_RATE_MASTER_RELATIVE_PATH = ("data", "role_rates.enc")


class RoleRateMasterError(Exception):
    pass


class RoleRateMasterDecryptionError(RoleRateMasterError):
    pass


class RoleRateMasterDuplicateError(RoleRateMasterError):
    pass


class RoleRateMasterValidationError(RoleRateMasterError):
    pass


class RoleRateMasterService:
    def __init__(
        self,
        master_path: Path | None = None,
        log_file: Path | None = None,
    ) -> None:
        self.master_path = master_path or project_path(*ROLE_RATE_MASTER_RELATIVE_PATH)
        self.logger = configure_error_logging(log_file)

    def save_role_rates(
        self,
        role_rates: list[RoleRate],
        license_id: str,
    ) -> None:
        try:
            self._validate_role_rates_for_save(role_rates)
            payload = json.dumps(
                self._to_payload(role_rates),
                ensure_ascii=False,
                separators=(",", ":"),
            )
            encrypted_payload = encrypt_text(payload, license_id)

            self.master_path.parent.mkdir(parents=True, exist_ok=True)
            self.master_path.write_bytes(encrypted_payload)
        except Exception as exc:
            log_exception(
                "role_rate_master_save",
                RoleRateMasterError(type(exc).__name__),
                self.master_path,
                self.logger,
            )
            raise

    def load_role_rates(self, license_id: str) -> list[RoleRate]:
        if not self.master_path.exists():
            return []

        encrypted_payload = self.master_path.read_bytes()
        try:
            payload_text = decrypt_text(encrypted_payload, license_id)
        except DecryptionError as exc:
            log_exception("role_rate_master_decrypt", exc, self.master_path, self.logger)
            raise RoleRateMasterDecryptionError(
                "role rate master could not be decrypted"
            ) from exc

        try:
            payload = json.loads(payload_text)
            role_rates = self._role_rates_from_payload(payload)
            self._validate_role_rates_for_save(role_rates)
            return role_rates
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            log_exception("role_rate_master_load", exc, self.master_path, self.logger)
            raise RoleRateMasterValidationError(
                "role rate master format is invalid"
            ) from exc

    def _validate_role_rates_for_save(self, role_rates: list[RoleRate]) -> None:
        if not isinstance(role_rates, list):
            raise RoleRateMasterValidationError("role_rates must be a list")
        if not all(isinstance(role_rate, RoleRate) for role_rate in role_rates):
            raise RoleRateMasterValidationError("role_rates must contain RoleRate")

        duplicate_groups = find_role_rate_duplicate_groups(role_rates)
        if duplicate_groups:
            raise RoleRateMasterDuplicateError("role_name is duplicated")

    def _to_payload(self, role_rates: list[RoleRate]) -> dict:
        return {
            "schema_version": ROLE_RATE_MASTER_SCHEMA_VERSION,
            "last_role_rate_no": _last_role_rate_no(role_rates),
            "role_rates": [
                {
                    "role_rate_id": role_rate.role_rate_id,
                    "is_active": role_rate.is_active,
                    "role_name": role_rate.role_name,
                    "hourly_rate": role_rate.hourly_rate,
                    "sort_order": role_rate.sort_order,
                }
                for role_rate in role_rates
            ],
        }

    def _role_rates_from_payload(self, payload: dict) -> list[RoleRate]:
        if not isinstance(payload, dict):
            raise ValueError("role rate master payload must be an object")
        if payload.get("schema_version") != ROLE_RATE_MASTER_SCHEMA_VERSION:
            raise ValueError("unsupported role rate master schema_version")

        role_rates = payload.get("role_rates")
        if not isinstance(role_rates, list):
            raise ValueError("role_rates must be a list")

        loaded_role_rates = []
        for item in role_rates:
            if not isinstance(item, dict):
                raise ValueError("role rate item must be an object")
            loaded_role_rates.append(
                RoleRate(
                    role_rate_id=item["role_rate_id"],
                    is_active=item["is_active"],
                    role_name=item["role_name"],
                    hourly_rate=item["hourly_rate"],
                    sort_order=item.get("sort_order"),
                )
            )
        return loaded_role_rates


def _last_role_rate_no(role_rates: list[RoleRate]) -> int:
    last_no = 0
    for role_rate in role_rates:
        match = re.fullmatch(r"R-(\d{6})", role_rate.role_rate_id)
        if match:
            last_no = max(last_no, int(match.group(1)))
    return last_no
