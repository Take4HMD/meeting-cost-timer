from dataclasses import dataclass
from datetime import datetime

from app.models.common import (
    effective_meeting_name,
    require_calculation_mode,
    require_datetime,
    require_non_negative_int,
    require_non_negative_number,
    require_positive_int,
    require_string,
)


@dataclass(slots=True)
class MeetingStartSettings:
    meeting_name: str
    calculation_mode: str
    total_hourly_rate: int

    def __post_init__(self) -> None:
        require_string(self.meeting_name, "meeting_name", allow_empty=True)
        require_calculation_mode(self.calculation_mode)
        require_positive_int(self.total_hourly_rate, "total_hourly_rate")

    @property
    def display_meeting_name(self) -> str:
        return effective_meeting_name(self.meeting_name)


@dataclass(slots=True)
class MeetingResult:
    meeting_name: str
    calculation_mode: str
    start_datetime: datetime
    end_datetime: datetime
    actual_count_seconds: int
    total_hourly_rate: int
    meeting_cost: int | float

    def __post_init__(self) -> None:
        require_string(self.meeting_name, "meeting_name", allow_empty=True)
        require_calculation_mode(self.calculation_mode)
        require_datetime(self.start_datetime, "start_datetime")
        require_datetime(self.end_datetime, "end_datetime")
        if self.end_datetime < self.start_datetime:
            raise ValueError("end_datetime must not be earlier than start_datetime")
        require_non_negative_int(self.actual_count_seconds, "actual_count_seconds")
        require_positive_int(self.total_hourly_rate, "total_hourly_rate")
        require_non_negative_number(self.meeting_cost, "meeting_cost")

    @property
    def display_meeting_name(self) -> str:
        return effective_meeting_name(self.meeting_name)
