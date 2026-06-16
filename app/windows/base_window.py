from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow

from app.utils.ui_loader import load_ui


class UiWindow(QMainWindow):
    ui_file_name: str

    def __init__(self) -> None:
        super().__init__()
        load_ui(self.ui_file_name, self)
