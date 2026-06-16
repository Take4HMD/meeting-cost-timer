from dataclasses import dataclass

from app.models.common import (
    require_optional_positive_int,
    require_positive_int,
    require_string,
)


@dataclass(slots=True)
class RoleRate:
    role_rate_id: str
    is_active: bool
    role_name: str
    hourly_rate: int
    sort_order: int | None = None

    def __post_init__(self) -> None:
        require_string(self.role_rate_id, "role_rate_id")
        if not isinstance(self.is_active, bool):
            raise ValueError("is_active must be a boolean")
        require_string(self.role_name, "role_name")
        require_positive_int(self.hourly_rate, "hourly_rate")
        require_optional_positive_int(self.sort_order, "sort_order")
