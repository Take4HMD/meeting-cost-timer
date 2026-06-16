from datetime import datetime


UNSET_MEETING_NAME = "名称未設定会議"


CALCULATION_MODE_PRECISE = "precise"
CALCULATION_MODE_SIMPLE = "simple"
CALCULATION_MODE_DISPLAY_DATA = "display_data"
CALCULATION_MODE_DIRECT = "direct"

CALCULATION_MODES = {
    CALCULATION_MODE_PRECISE,
    CALCULATION_MODE_SIMPLE,
    CALCULATION_MODE_DISPLAY_DATA,
    CALCULATION_MODE_DIRECT,
}


def require_string(value: str, field_name: str, allow_empty: bool = False) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not allow_empty and not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def require_positive_int(value: int, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    if value < 1:
        raise ValueError(f"{field_name} must be at least 1")


def require_non_negative_int(value: int, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be at least 0")


def require_non_negative_number(value: int | float, field_name: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be a number")
    if value < 0:
        raise ValueError(f"{field_name} must be at least 0")


def require_optional_positive_int(value: int | None, field_name: str) -> None:
    if value is None:
        return
    require_positive_int(value, field_name)


def require_datetime(value: datetime, field_name: str) -> None:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")


def require_calculation_mode(value: str) -> None:
    if value not in CALCULATION_MODES:
        raise ValueError("calculation_mode is invalid")


def effective_meeting_name(meeting_name: str) -> str:
    require_string(meeting_name, "meeting_name", allow_empty=True)
    normalized = meeting_name.strip()
    if normalized:
        return normalized
    return UNSET_MEETING_NAME
