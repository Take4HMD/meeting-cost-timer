from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Sequence

from app.models.participant import Participant
from app.models.role_rate import RoleRate


PausePeriod = tuple[datetime, datetime]
RoleRateCount = tuple[RoleRate, int]


def calculate_precise_total_hourly_rate(participants: Iterable[Participant]) -> int:
    selected_participants = list(participants)
    if not selected_participants:
        raise ValueError("participants must not be empty")

    total_hourly_rate = 0
    for participant in selected_participants:
        if not participant.is_active:
            raise ValueError("participants must be active")
        total_hourly_rate += participant.hourly_rate

    if total_hourly_rate < 1:
        raise ValueError("total_hourly_rate must be at least 1")
    return total_hourly_rate


def calculate_simple_total_hourly_rate(role_rate_counts: Iterable[RoleRateCount]) -> int:
    entries = list(role_rate_counts)
    if not entries:
        raise ValueError("role_rate_counts must not be empty")

    total_people = 0
    total_hourly_rate = 0
    for role_rate, count in entries:
        if not role_rate.is_active:
            raise ValueError("role_rates must be active")
        _require_non_negative_integer(count, "count")
        total_people += count
        total_hourly_rate += role_rate.hourly_rate * count

    if total_people < 1:
        raise ValueError("total people must be at least 1")
    if total_hourly_rate < 1:
        raise ValueError("total_hourly_rate must be at least 1")
    return total_hourly_rate


def validate_direct_total_hourly_rate(value: int | str) -> int:
    if isinstance(value, bool):
        raise ValueError("total_hourly_rate must be an integer")

    if isinstance(value, int):
        total_hourly_rate = value
    elif isinstance(value, str):
        normalized = value.strip().replace(",", "")
        if not normalized.isdecimal():
            raise ValueError("total_hourly_rate must be an integer")
        total_hourly_rate = int(normalized)
    else:
        raise ValueError("total_hourly_rate must be an integer")

    if total_hourly_rate < 1:
        raise ValueError("total_hourly_rate must be at least 1")
    return total_hourly_rate


def calculate_meeting_cost(total_hourly_rate: int, actual_count_seconds: int) -> float:
    _require_positive_integer(total_hourly_rate, "total_hourly_rate")
    _require_non_negative_integer(actual_count_seconds, "actual_count_seconds")
    return total_hourly_rate / 3600 * actual_count_seconds


def round_meeting_cost_for_output(meeting_cost: int | float) -> int:
    if not isinstance(meeting_cost, (int, float)) or isinstance(meeting_cost, bool):
        raise ValueError("meeting_cost must be a number")
    if meeting_cost < 0:
        raise ValueError("meeting_cost must be at least 0")

    return int(
        Decimal(str(meeting_cost)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )


def calculate_actual_count_seconds(
    start_datetime: datetime,
    end_datetime: datetime,
    pause_periods: Sequence[PausePeriod] | None = None,
) -> int:
    _require_datetime(start_datetime, "start_datetime")
    _require_datetime(end_datetime, "end_datetime")
    if end_datetime < start_datetime:
        raise ValueError("end_datetime must not be earlier than start_datetime")

    elapsed_seconds = int((end_datetime - start_datetime).total_seconds())
    pause_seconds = _calculate_pause_seconds(
        start_datetime,
        end_datetime,
        pause_periods or (),
    )
    return elapsed_seconds - pause_seconds


def _calculate_pause_seconds(
    start_datetime: datetime,
    end_datetime: datetime,
    pause_periods: Sequence[PausePeriod],
) -> int:
    normalized_periods: list[PausePeriod] = []
    for pause_start, pause_end in pause_periods:
        _require_datetime(pause_start, "pause_start")
        _require_datetime(pause_end, "pause_end")
        if pause_end < pause_start:
            raise ValueError("pause_end must not be earlier than pause_start")

        clipped_start = max(pause_start, start_datetime)
        clipped_end = min(pause_end, end_datetime)
        if clipped_end > clipped_start:
            normalized_periods.append((clipped_start, clipped_end))

    if not normalized_periods:
        return 0

    normalized_periods.sort(key=lambda period: period[0])
    merged_periods: list[PausePeriod] = []
    for period_start, period_end in normalized_periods:
        if not merged_periods:
            merged_periods.append((period_start, period_end))
            continue

        last_start, last_end = merged_periods[-1]
        if period_start <= last_end:
            merged_periods[-1] = (last_start, max(last_end, period_end))
        else:
            merged_periods.append((period_start, period_end))

    return int(
        sum(
            (period_end - period_start).total_seconds()
            for period_start, period_end in merged_periods
        )
    )


def _require_positive_integer(value: int, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    if value < 1:
        raise ValueError(f"{field_name} must be at least 1")


def _require_non_negative_integer(value: int, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be at least 0")


def _require_datetime(value: datetime, field_name: str) -> None:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
