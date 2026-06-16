from app.utils.logging_config import configure_error_logging, log_exception


def test_log_exception_writes_error_log(tmp_path):
    log_file = tmp_path / "logs" / "error.log"
    logger = configure_error_logging(log_file)

    try:
        raise ValueError("sample failure")
    except ValueError as exc:
        log_exception("sample_process", exc, "config/app_settings.json", logger)

    content = log_file.read_text(encoding="utf-8")
    assert "sample_process" in content
    assert "ValueError" in content
    assert "sample failure" in content


def test_log_exception_masks_license_id(tmp_path):
    log_file = tmp_path / "logs" / "error.log"
    logger = configure_error_logging(log_file)

    try:
        raise ValueError("license_id=LIC-ABCD-1234")
    except ValueError as exc:
        log_exception("sample_process", exc, None, logger)

    content = log_file.read_text(encoding="utf-8")
    assert "LIC-ABCD-1234" not in content
    assert "license_id=****" in content
