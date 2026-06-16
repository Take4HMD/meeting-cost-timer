import logging
import re
from pathlib import Path

from app.utils.paths import project_path


LOGGER_NAME = "meeting_cost_timer"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def configure_error_logging(log_file: Path | None = None) -> logging.Logger:
    target = log_file or project_path("logs", "error.log")
    target.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.ERROR)
    logger.propagate = False

    target_resolved = target.resolve()
    for handler in list(logger.handlers):
        if isinstance(handler, logging.FileHandler):
            handler_path = Path(handler.baseFilename).resolve()
            if handler_path == target_resolved:
                return logger

    handler = logging.FileHandler(target, encoding="utf-8")
    handler.setLevel(logging.ERROR)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(handler)
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    configure_error_logging()
    if not name:
        return logging.getLogger(LOGGER_NAME)
    return logging.getLogger(f"{LOGGER_NAME}.{name}")


def log_exception(
    process_name: str,
    exception: Exception,
    target_file: str | Path | None = None,
    logger: logging.Logger | None = None,
) -> None:
    active_logger = logger or configure_error_logging()
    active_logger.error(
        "process=%s target=%s error_type=%s error=%s",
        process_name,
        _safe_value(str(target_file or "")),
        type(exception).__name__,
        _safe_value(str(exception)),
    )


def _safe_value(value: str) -> str:
    value = re.sub(r"LIC-[A-Z0-9-]+", "LIC-****", value, flags=re.IGNORECASE)
    value = re.sub(r"license_id[=:]\s*[^,\s]+", "license_id=****", value, flags=re.IGNORECASE)
    return value
