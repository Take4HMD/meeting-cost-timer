from app.models.participant import Participant
from app.models.role_rate import RoleRate
from app.services.duplicate_service import (
    find_participant_duplicate_confirmation_groups,
    find_participant_duplicate_error_groups,
    find_role_rate_duplicate_groups,
    has_participant_duplicates,
    has_role_rate_duplicates,
)


def _participant(
    participant_id: str,
    name: str = "Yamada Taro",
    department: str = "Sales",
    position: str = "Manager",
    display_name: str = "",
) -> Participant:
    return Participant(
        participant_id=participant_id,
        is_active=True,
        name=name,
        department=department,
        position=position,
        display_name=display_name,
        hourly_rate=6000,
    )


def _role_rate(
    role_rate_id: str,
    role_name: str = "Manager",
) -> RoleRate:
    return RoleRate(
        role_rate_id=role_rate_id,
        is_active=True,
        role_name=role_name,
        hourly_rate=6000,
    )


def test_find_participant_duplicate_confirmation_groups_uses_name_department_position():
    participants = [
        _participant("P-000001", display_name="A"),
        _participant("P-000002", display_name="B"),
        _participant("P-000003", name="Sato Hanako"),
    ]

    groups = find_participant_duplicate_confirmation_groups(participants)

    assert len(groups) == 1
    assert groups[0].key == ("Yamada Taro", "Sales", "Manager")
    assert {item.participant_id for item in groups[0].items} == {
        "P-000001",
        "P-000002",
    }


def test_find_participant_duplicate_error_groups_uses_display_name_too():
    participants = [
        _participant("P-000001", display_name="A"),
        _participant("P-000002", display_name="A"),
        _participant("P-000003", display_name="B"),
    ]

    groups = find_participant_duplicate_error_groups(participants)

    assert len(groups) == 1
    assert groups[0].key == ("Yamada Taro", "Sales", "Manager", "A")
    assert {item.participant_id for item in groups[0].items} == {
        "P-000001",
        "P-000002",
    }


def test_participant_duplicate_error_groups_strip_key_parts():
    participants = [
        _participant("P-000001", name=" Yamada Taro ", display_name=" A "),
        _participant("P-000002", name="Yamada Taro", display_name="A"),
    ]

    assert has_participant_duplicates(participants)


def test_participant_duplicates_are_not_found_for_unique_identity_keys():
    participants = [
        _participant("P-000001", display_name="A"),
        _participant("P-000002", display_name="B"),
    ]

    assert not has_participant_duplicates(participants)


def test_find_role_rate_duplicate_groups_uses_role_name():
    role_rates = [
        _role_rate("R-000001"),
        _role_rate("R-000002"),
        _role_rate("R-000003", role_name="Staff"),
    ]

    groups = find_role_rate_duplicate_groups(role_rates)

    assert len(groups) == 1
    assert groups[0].key == ("Manager",)
    assert {item.role_rate_id for item in groups[0].items} == {
        "R-000001",
        "R-000002",
    }


def test_role_rate_duplicate_groups_strip_role_name():
    role_rates = [
        _role_rate("R-000001", role_name=" Manager "),
        _role_rate("R-000002", role_name="Manager"),
    ]

    assert has_role_rate_duplicates(role_rates)


def test_role_rate_duplicates_are_not_found_for_unique_role_names():
    role_rates = [
        _role_rate("R-000001", role_name="Manager"),
        _role_rate("R-000002", role_name="Staff"),
    ]

    assert not has_role_rate_duplicates(role_rates)
