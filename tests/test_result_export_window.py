import os
from datetime import datetime
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication, QFileDialog

from app.models.common import CALCULATION_MODE_SIMPLE
from app.models.meeting import MeetingResult
from app.windows.result_export_window import OUTPUT_FORMAT_CSV, ResultExportWindow


@pytest.fixture(scope="session")
def qt_application():
    application = QApplication.instance() or QApplication([])
    return application


class StubSettingsService:
    def __init__(self):
        self.saved_settings = None

    def save(self, settings):
        self.saved_settings = settings


def _meeting_result():
    return MeetingResult(
        meeting_name="Sales Meeting",
        calculation_mode=CALCULATION_MODE_SIMPLE,
        start_datetime=datetime(2026, 6, 4, 10, 0, 0),
        end_datetime=datetime(2026, 6, 4, 10, 10, 0),
        actual_count_seconds=600,
        total_hourly_rate=3600,
        meeting_cost=600,
    )


def test_result_export_window_receives_meeting_result_and_uses_csv_only(
    qt_application,
):
    result = _meeting_result()

    window = ResultExportWindow(meeting_result=result)

    assert window.meeting_result == result
    assert window.outputFormatComboBox.count() == 1
    assert window.outputFormatComboBox.currentData() == OUTPUT_FORMAT_CSV
    assert not window.outputFormatComboBox.isEnabled()
    window.close()


def test_result_export_window_applies_existing_last_output_dir(
    qt_application,
    tmp_path,
):
    settings = {
        "output_settings": {
            "last_output_dir": str(tmp_path),
            "default_format": "csv",
        }
    }

    window = ResultExportWindow(meeting_result=_meeting_result(), settings=settings)

    assert window.outputFolderLineEdit.text() == str(tmp_path)
    window.close()


def test_result_export_window_selects_output_folder(
    qt_application,
    monkeypatch,
    tmp_path,
):
    selected_path = str(tmp_path / "exports")
    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: selected_path,
    )
    window = ResultExportWindow(meeting_result=_meeting_result())

    window.choose_output_folder()

    assert window.outputFolderLineEdit.text() == selected_path
    window.close()


def test_result_export_window_exports_csv_and_saves_last_output_dir(
    qt_application,
    tmp_path,
):
    result = _meeting_result()
    settings = {"output_settings": {"last_output_dir": "", "default_format": "csv"}}
    settings_service = StubSettingsService()
    export_calls = []

    def csv_exporter(meeting_result, output_path):
        export_calls.append((meeting_result, output_path))

    window = ResultExportWindow(
        meeting_result=result,
        settings=settings,
        settings_service=settings_service,
        csv_exporter=csv_exporter,
        now_provider=lambda: datetime(2026, 6, 4, 12, 34, 56),
    )
    messages = []
    window._show_information = lambda title, message: messages.append((title, message))
    window._show_error = pytest.fail
    window.outputFolderLineEdit.setText(str(tmp_path))

    output_path = window.execute_export()

    assert output_path == Path(str(tmp_path)) / "meeting_cost_20260604_123456.csv"
    assert export_calls == [(result, output_path)]
    assert settings["output_settings"]["last_output_dir"] == str(tmp_path)
    assert settings_service.saved_settings == settings
    assert messages
    window.close()


def test_result_export_window_shows_error_without_meeting_result(
    qt_application,
    tmp_path,
):
    errors = []
    window = ResultExportWindow(meeting_result=None)
    window._show_error = lambda title, message: errors.append((title, message))
    window.outputFolderLineEdit.setText(str(tmp_path))

    output_path = window.execute_export()

    assert output_path is None
    assert errors
    window.close()


def test_result_export_window_logs_unexpected_export_error(
    qt_application,
    tmp_path,
):
    errors = []
    log_calls = []

    def csv_exporter(meeting_result, output_path):
        raise RuntimeError("unexpected export failure")

    def exception_logger(process_name, exception, target_file, logger):
        log_calls.append((process_name, exception, target_file, logger))

    window = ResultExportWindow(
        meeting_result=_meeting_result(),
        csv_exporter=csv_exporter,
        exception_logger=exception_logger,
        now_provider=lambda: datetime(2026, 6, 4, 12, 34, 56),
    )
    window._show_error = lambda title, message: errors.append((title, message))
    window.outputFolderLineEdit.setText(str(tmp_path))

    output_path = window.execute_export()

    assert output_path is None
    assert errors
    assert len(log_calls) == 1
    process_name, exception, target_file, logger = log_calls[0]
    assert process_name == "result_export"
    assert isinstance(exception, RuntimeError)
    assert target_file == Path(str(tmp_path)) / "meeting_cost_20260604_123456.csv"
    assert logger is not None
    window.close()
