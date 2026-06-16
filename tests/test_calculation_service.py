from datetime import datetime, timedelta

import pytest

from app.models.participant import Participant
from app.models.role_rate import RoleRate
from app.services.calculation_service import (
    calculate_actual_count_seconds,
    calculate_meeting_cost,
    calculate_precise_total_hourly_rate,
    calculate_simple_total_hourly_rate,
    round_meeting_cost_for_output,
    validate_direct_total_hourly_rate,
)


def test_calculate_precise_total_hourly_rate_sums_active_participants():
    participants = [
        Participant(
            participant_id="P-000001",
            is_active=True,
            name="Yamada Taro",
            hourly_rate=6000,
        ),
        Participant(
            participant_id="P-000002",
            is_active=True,
            name="Sato Hanako",
            hourly_rate=4000,
        ),
    ]

    assert calculate_precise_total_hourly_rate(participants) == 10000


def test_calculate_precise_total_hourly_rate_rejects_empty_or_inactive():
    with pytest.raises(ValueError):
        calculate_precise_total_hourly_rate([])

    with pytest.raises(ValueError):
        calculate_precise_total_hourly_rate(
            [
                Participant(
                    participant_id="P-000001",
                    is_active=False,
                    name="Yamada Taro",
                    hourly_rate=6000,
                )
            ]
        )


def test_calculate_simple_total_hourly_rate_sums_role_rates_times_counts():
    role_rates = [
        (
            RoleRate(
                role_rate_id="R-000001",
                is_active=True,
                role_name="Manager",
                hourly_rate=6000,
            ),
            2,
        ),
        (
            RoleRate(
                role_rate_id="R-000002",
                is_active=True,
                role_name="Staff",
                hourly_rate=3000,
            ),
            3,
        ),
    ]

    assert calculate_simple_total_hourly_rate(role_rates) == 21000


def test_calculate_simple_total_hourly_rate_rejects_invalid_counts():
    role_rate = RoleRate(
        role_rate_id="R-000001",
        is_active=True,
        role_name="Manager",
        hourly_rate=6000,
    )

    with pytest.raises(ValueError):
        calculate_simple_total_hourly_rate([(role_rate, 0)])

    with pytest.raises(ValueError):
        calculate_simple_total_hourly_rate([(role_rate, -1)])

    with pytest.raises(ValueError):
        calculate_simple_total_hourly_rate([(role_rate, 1.5)])


def test_calculate_simple_total_hourly_rate_rejects_inactive_role_rate():
    role_rate = RoleRate(
        role_rate_id="R-000001",
        is_active=False,
        role_name="Manager",
        hourly_rate=6000,
    )

    with pytest.raises(ValueError):
        calculate_simple_total_hourly_rate([(role_rate, 1)])


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (12000, 12000),
        ("12000", 12000),
        ("12,000", 12000),
        (" 12,000 ", 12000),
    ],
)
def test_validate_direct_total_hourly_rate_accepts_valid_values(value, expected):
    assert validate_direct_total_hourly_rate(value) == expected


@pytest.mark.parametrize("value", [0, -1, "0", "12.5", "abc", "", True])
def test_validate_direct_total_hourly_rate_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        validate_direct_total_hourly_rate(value)


def test_calculate_meeting_cost_uses_hourly_rate_and_actual_seconds():
    assert calculate_meeting_cost(7201, 1800) == 3600.5


def test_calculate_meeting_cost_rejects_invalid_values():
    with pytest.raises(ValueError):
        calculate_meeting_cost(0, 1800)

    with pytest.raises(ValueError):
        calculate_meeting_cost(7200, -1)


@pytest.mark.parametrize(
    ("meeting_cost", "expected"),
    [
        (0, 0),
        (1234, 1234),
        (1234.4, 1234),
        (1234.5, 1235),
        (1234.6, 1235),
    ],
)
def test_round_meeting_cost_for_output_rounds_to_integer_yen(
    meeting_cost,
    expected,
):
    assert round_meeting_cost_for_output(meeting_cost) == expected


@pytest.mark.parametrize("meeting_cost", [-0.1, -1, "100", True])
def test_round_meeting_cost_for_output_rejects_invalid_values(meeting_cost):
    with pytest.raises(ValueError):
        round_meeting_cost_for_output(meeting_cost)


def test_calculate_actual_count_seconds_excludes_pause_periods():
    start_datetime = datetime(2026, 6, 4, 10, 0, 0)
    end_datetime = start_datetime + timedelta(minutes=30)
    pause_periods = [
        (
            start_datetime + timedelta(minutes=5),
            start_datetime + timedelta(minutes=10),
        ),
        (
            start_datetime + timedelta(minutes=20),
            start_datetime + timedelta(minutes=25),
        ),
    ]

    assert (
        calculate_actual_count_seconds(start_datetime, end_datetime, pause_periods)
        == 1200
    )


def test_calculate_actual_count_seconds_merges_overlapping_pause_periods():
    start_datetime = datetime(2026, 6, 4, 10, 0, 0)
    end_datetime = start_datetime + timedelta(minutes=30)
    pause_periods = [
        (
            start_datetime + timedelta(minutes=5),
            start_datetime + timedelta(minutes=15),
        ),
        (
            start_datetime + timedelta(minutes=10),
            start_datetime + timedelta(minutes=20),
        ),
    ]

    assert (
        calculate_actual_count_seconds(start_datetime, end_datetime, pause_periods)
        == 900
    )


def test_calculate_actual_count_seconds_clips_pause_periods_to_meeting_time():
    start_datetime = datetime(2026, 6, 4, 10, 0, 0)
    end_datetime = start_datetime + timedelta(minutes=30)
    pause_periods = [
        (
            start_datetime - timedelta(minutes=5),
            start_datetime + timedelta(minutes=5),
        ),
        (
            end_datetime - timedelta(minutes=5),
            end_datetime + timedelta(minutes=5),
        ),
    ]

    assert (
        calculate_actual_count_seconds(start_datetime, end_datetime, pause_periods)
        == 1200
    )


def test_calculate_actual_count_seconds_rejects_invalid_periods():
    start_datetime = datetime(2026, 6, 4, 10, 0, 0)
    end_datetime = start_datetime + timedelta(minutes=30)

    with pytest.raises(ValueError):
        calculate_actual_count_seconds(end_datetime, start_datetime)

    with pytest.raises(ValueError):
        calculate_actual_count_seconds(
            start_datetime,
            end_datetime,
            [(end_datetime, start_datetime)],
        )
