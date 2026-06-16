from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from app.models.participant import Participant
from app.models.role_rate import RoleRate


ParticipantBaseKey = tuple[str, str, str]
ParticipantIdentityKey = tuple[str, str, str, str]
RoleRateKey = str


@dataclass(frozen=True, slots=True)
class DuplicateGroup:
    key: tuple[str, ...]
    items: tuple[object, ...]


def find_participant_duplicate_confirmation_groups(
    participants: Iterable[Participant],
) -> list[DuplicateGroup]:
    grouped: dict[ParticipantBaseKey, list[Participant]] = defaultdict(list)
    for participant in participants:
        grouped[_participant_base_key(participant)].append(participant)

    return _to_duplicate_groups(grouped)


def find_participant_duplicate_error_groups(
    participants: Iterable[Participant],
) -> list[DuplicateGroup]:
    grouped: dict[ParticipantIdentityKey, list[Participant]] = defaultdict(list)
    for participant in participants:
        grouped[participant.identity_key].append(participant)

    return _to_duplicate_groups(grouped)


def find_role_rate_duplicate_groups(
    role_rates: Iterable[RoleRate],
) -> list[DuplicateGroup]:
    grouped: dict[RoleRateKey, list[RoleRate]] = defaultdict(list)
    for role_rate in role_rates:
        grouped[_normalize_key_part(role_rate.role_name)].append(role_rate)

    return _to_duplicate_groups(grouped)


def has_participant_duplicates(participants: Iterable[Participant]) -> bool:
    return bool(find_participant_duplicate_error_groups(participants))


def has_role_rate_duplicates(role_rates: Iterable[RoleRate]) -> bool:
    return bool(find_role_rate_duplicate_groups(role_rates))


def _participant_base_key(participant: Participant) -> ParticipantBaseKey:
    name, department, position, _display_name = participant.identity_key
    return (name, department, position)


def _normalize_key_part(value: str) -> str:
    return value.strip()


def _to_duplicate_groups(grouped: dict) -> list[DuplicateGroup]:
    duplicate_groups = []
    for key, items in grouped.items():
        if len(items) > 1:
            normalized_key = key if isinstance(key, tuple) else (key,)
            duplicate_groups.append(
                DuplicateGroup(
                    key=normalized_key,
                    items=tuple(items),
                )
            )
    return duplicate_groups
