from dataclasses import dataclass

from app.models.common import (
    require_optional_positive_int,
    require_positive_int,
    require_string,
)


@dataclass(slots=True, kw_only=True)
class Participant:
    participant_id: str
    is_active: bool
    name: str
    hourly_rate: int
    department: str = ""
    position: str = ""
    display_name: str = ""
    sort_order: int | None = None

    def __post_init__(self) -> None:
        require_string(self.participant_id, "participant_id")
        if not isinstance(self.is_active, bool):
            raise ValueError("is_active must be a boolean")
        require_string(self.name, "name")
        require_string(self.department, "department", allow_empty=True)
        require_string(self.position, "position", allow_empty=True)
        require_string(self.display_name, "display_name", allow_empty=True)
        require_positive_int(self.hourly_rate, "hourly_rate")
        require_optional_positive_int(self.sort_order, "sort_order")

    @property
    def identity_key(self) -> tuple[str, str, str, str]:
        return (
            self.name.strip(),
            self.department.strip(),
            self.position.strip(),
            self.display_name.strip(),
        )
