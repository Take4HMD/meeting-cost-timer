from __future__ import annotations

from pathlib import Path

from PyQt6 import uic
from PyQt6.QtWidgets import QWidget

from app.utils.paths import resource_path


def ui_path(file_name: str) -> Path:
    return resource_path(f"app/ui/{file_name}")


def load_ui(file_name: str, instance: QWidget) -> None:
    uic.loadUi(ui_path(file_name), instance)
