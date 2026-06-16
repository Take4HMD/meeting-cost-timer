import pytest

from app.services.license_id_generator import generate_license_id, generate_license_ids
from app.services.license_settings_service import validate_license_id


def test_generate_license_id_returns_valid_license_id_for_issue_month():
    license_id = generate_license_id("202606")

    assert license_id.startswith("MCT-202606-")
    assert validate_license_id(license_id) == license_id


def test_generate_license_ids_returns_requested_unique_values():
    license_ids = generate_license_ids(20, "202606")

    assert len(license_ids) == 20
    assert len(set(license_ids)) == 20
    assert all(validate_license_id(license_id) == license_id for license_id in license_ids)


@pytest.mark.parametrize("issue_yyyymm", ["2026", "202600", "202613", "ABCDEF"])
def test_generate_license_id_rejects_invalid_issue_month(issue_yyyymm):
    with pytest.raises(ValueError):
        generate_license_id(issue_yyyymm)


def test_generate_license_ids_rejects_zero_count():
    with pytest.raises(ValueError):
        generate_license_ids(0, "202606")
