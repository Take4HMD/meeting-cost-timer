from __future__ import annotations

from datetime import datetime
import secrets

from app.services.license_settings_service import (
    LICENSE_ID_PREFIX,
    LICENSE_ID_RANDOM_ALPHABET,
    calculate_license_check_digit,
    validate_license_id,
)


def generate_license_id(issue_yyyymm: str | None = None) -> str:
    if issue_yyyymm is None:
        issue_yyyymm = datetime.now().strftime("%Y%m")
    _validate_issue_yyyymm(issue_yyyymm)

    random_part_1 = _generate_random_part()
    random_part_2 = _generate_random_part()
    body = f"{LICENSE_ID_PREFIX}{issue_yyyymm}{random_part_1}{random_part_2}"
    check_digit = calculate_license_check_digit(body)
    license_id = (
        f"{LICENSE_ID_PREFIX}-{issue_yyyymm}-"
        f"{random_part_1}-{random_part_2}-{check_digit}"
    )
    return validate_license_id(license_id)


def generate_license_ids(count: int, issue_yyyymm: str | None = None) -> list[str]:
    if count < 1:
        raise ValueError("count must be 1 or greater")

    license_ids = set()
    while len(license_ids) < count:
        license_ids.add(generate_license_id(issue_yyyymm))
    return sorted(license_ids)


def _generate_random_part() -> str:
    return "".join(secrets.choice(LICENSE_ID_RANDOM_ALPHABET) for _ in range(4))


def _validate_issue_yyyymm(issue_yyyymm: str) -> None:
    if len(issue_yyyymm) != 6 or not issue_yyyymm.isdecimal():
        raise ValueError("issue_yyyymm must be YYYYMM")
    issue_month = int(issue_yyyymm[4:6])
    if issue_month < 1 or issue_month > 12:
        raise ValueError("issue_yyyymm month must be 01-12")
