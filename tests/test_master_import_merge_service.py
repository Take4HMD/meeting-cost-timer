from app.models.participant import Participant
from app.models.role_rate import RoleRate
from app.services.master_import_merge_service import (
    merge_imported_participants,
    merge_imported_role_rates,
)


def _participant(
    participant_id,
    name="Yamada Taro",
    department="Sales",
    position="Manager",
    display_name="",
    hourly_rate=6000,
):
    return Participant(
        participant_id=participant_id,
        is_active=True,
        name=name,
        department=department,
        position=position,
        display_name=display_name,
        hourly_rate=hourly_rate,
    )


def _role_rate(role_rate_id, role_name="Manager", hourly_rate=6000):
    return RoleRate(
        role_rate_id=role_rate_id,
        is_active=True,
        role_name=role_name,
        hourly_rate=hourly_rate,
    )


def test_merge_imported_participants_updates_matching_key_and_keeps_existing_id():
    existing = [_participant("P-000010", hourly_rate=6000)]
    imported = [_participant("P-000001", hourly_rate=8000)]

    result = merge_imported_participants(existing, imported)

    assert result.added_count == 0
    assert result.updated_count == 1
    assert result.items == [_participant("P-000010", hourly_rate=8000)]


def test_merge_imported_participants_adds_new_and_does_not_delete_missing_existing():
    existing = [
        _participant("P-000010", name="Yamada Taro"),
        _participant("P-000011", name="Sato Hanako"),
    ]
    imported = [_participant("P-000001", name="Suzuki Jiro", hourly_rate=7000)]

    result = merge_imported_participants(existing, imported)

    assert result.added_count == 1
    assert result.updated_count == 0
    assert result.items == [
        existing[0],
        existing[1],
        _participant("P-000012", name="Suzuki Jiro", hourly_rate=7000),
    ]


def test_merge_imported_role_rates_updates_matching_key_and_keeps_existing_id():
    existing = [_role_rate("R-000010", role_name="Manager", hourly_rate=6000)]
    imported = [_role_rate("R-000001", role_name=" Manager ", hourly_rate=8000)]

    result = merge_imported_role_rates(existing, imported)

    assert result.added_count == 0
    assert result.updated_count == 1
    assert result.items == [
        _role_rate("R-000010", role_name=" Manager ", hourly_rate=8000)
    ]


def test_merge_imported_role_rates_adds_new_and_does_not_delete_missing_existing():
    existing = [
        _role_rate("R-000010", role_name="Manager"),
        _role_rate("R-000011", role_name="Staff"),
    ]
    imported = [_role_rate("R-000001", role_name="Director", hourly_rate=9000)]

    result = merge_imported_role_rates(existing, imported)

    assert result.added_count == 1
    assert result.updated_count == 0
    assert result.items == [
        existing[0],
        existing[1],
        _role_rate("R-000012", role_name="Director", hourly_rate=9000),
    ]
