from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Generic, TypeVar

from app.models.participant import Participant
from app.models.role_rate import RoleRate


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class MasterImportMergeResult(Generic[T]):
    items: list[T]
    added_count: int
    updated_count: int
    error_count: int = 0


def merge_imported_participants(
    existing_participants: list[Participant],
    imported_participants: list[Participant],
) -> MasterImportMergeResult[Participant]:
    existing_by_key = {
        participant.identity_key: participant for participant in existing_participants
    }
    imported_keys = [
        participant.identity_key for participant in imported_participants
    ]
    next_no = _next_no(
        [participant.participant_id for participant in existing_participants],
        "P",
    )
    imported_by_key = {}
    added_count = 0
    updated_count = 0

    for imported_participant in imported_participants:
        key = imported_participant.identity_key
        existing_participant = existing_by_key.get(key)
        if existing_participant is None:
            participant_id = f"P-{next_no:06d}"
            next_no += 1
            added_count += 1
        else:
            participant_id = existing_participant.participant_id
            updated_count += 1

        imported_by_key[key] = _copy_participant_with_id(
            imported_participant,
            participant_id,
        )

    merged_participants = [
        imported_by_key.get(participant.identity_key, participant)
        for participant in existing_participants
    ]
    merged_participants.extend(
        imported_by_key[key]
        for key in imported_keys
        if key not in existing_by_key
    )

    return MasterImportMergeResult(
        items=merged_participants,
        added_count=added_count,
        updated_count=updated_count,
    )


def merge_imported_role_rates(
    existing_role_rates: list[RoleRate],
    imported_role_rates: list[RoleRate],
) -> MasterImportMergeResult[RoleRate]:
    existing_by_key = {
        _role_rate_key(role_rate): role_rate for role_rate in existing_role_rates
    }
    imported_keys = [_role_rate_key(role_rate) for role_rate in imported_role_rates]
    next_no = _next_no([role_rate.role_rate_id for role_rate in existing_role_rates], "R")
    imported_by_key = {}
    added_count = 0
    updated_count = 0

    for imported_role_rate in imported_role_rates:
        key = _role_rate_key(imported_role_rate)
        existing_role_rate = existing_by_key.get(key)
        if existing_role_rate is None:
            role_rate_id = f"R-{next_no:06d}"
            next_no += 1
            added_count += 1
        else:
            role_rate_id = existing_role_rate.role_rate_id
            updated_count += 1

        imported_by_key[key] = _copy_role_rate_with_id(
            imported_role_rate,
            role_rate_id,
        )

    merged_role_rates = [
        imported_by_key.get(_role_rate_key(role_rate), role_rate)
        for role_rate in existing_role_rates
    ]
    merged_role_rates.extend(
        imported_by_key[key]
        for key in imported_keys
        if key not in existing_by_key
    )

    return MasterImportMergeResult(
        items=merged_role_rates,
        added_count=added_count,
        updated_count=updated_count,
    )


def _copy_participant_with_id(
    participant: Participant,
    participant_id: str,
) -> Participant:
    return Participant(
        participant_id=participant_id,
        is_active=participant.is_active,
        name=participant.name,
        department=participant.department,
        position=participant.position,
        display_name=participant.display_name,
        hourly_rate=participant.hourly_rate,
        sort_order=participant.sort_order,
    )


def _copy_role_rate_with_id(role_rate: RoleRate, role_rate_id: str) -> RoleRate:
    return RoleRate(
        role_rate_id=role_rate_id,
        is_active=role_rate.is_active,
        role_name=role_rate.role_name,
        hourly_rate=role_rate.hourly_rate,
        sort_order=role_rate.sort_order,
    )


def _role_rate_key(role_rate: RoleRate) -> str:
    return role_rate.role_name.strip()


def _next_no(item_ids: list[str], prefix: str) -> int:
    last_no = 0
    pattern = re.compile(rf"{re.escape(prefix)}-(\d{{6}})")
    for item_id in item_ids:
        match = pattern.fullmatch(item_id)
        if match:
            last_no = max(last_no, int(match.group(1)))
    return last_no + 1
