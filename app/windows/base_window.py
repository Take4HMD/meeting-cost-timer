from __future__ import annotations

from PyQt6.QtWidgets import QLayout, QMainWindow

from app.utils.ui_loader import load_ui


UI_MINIMUM_SIZES = {
    "main_menu.ui": (420, 360),
    "license_settings.ui": (420, 220),
    "master_menu.ui": (360, 300),
    "participant_master.ui": (900, 520),
    "role_rate_master.ui": (760, 440),
    "master_import.ui": (680, 480),
    "master_export.ui": (720, 220),
    "meeting_start_settings.ui": (520, 260),
    "precise_participant_selection.ui": (820, 520),
    "simple_role_count.ui": (560, 420),
    "mcd_import.ui": (640, 180),
    "direct_input.ui": (620, 280),
    "count_display.ui": (480, 180),
    "result_export.ui": (720, 220),
    "display_settings.ui": (520, 360),
}
WINDOW_CONTENT_MARGINS = (16, 16, 16, 16)
WINDOW_LAYOUT_SPACING = 10


class UiWindow(QMainWindow):
    ui_file_name: str

    def __init__(self) -> None:
        super().__init__()
        load_ui(self.ui_file_name, self)
        self._apply_readable_layout_spacing()
        self._apply_minimum_readable_size()

    def _apply_minimum_readable_size(self) -> None:
        minimum_size = UI_MINIMUM_SIZES.get(self.ui_file_name)
        if minimum_size is None:
            return

        minimum_width, minimum_height = minimum_size
        self.setMinimumSize(minimum_width, minimum_height)
        self.resize(minimum_width, minimum_height)

    def _apply_readable_layout_spacing(self) -> None:
        central_widget = self.centralWidget()
        if central_widget is None:
            return

        root_layout = central_widget.layout()
        if root_layout is None:
            return

        root_layout.setContentsMargins(*WINDOW_CONTENT_MARGINS)
        self._apply_layout_spacing(root_layout)

    def _apply_layout_spacing(self, layout: QLayout) -> None:
        layout.setSpacing(WINDOW_LAYOUT_SPACING)

        for index in range(layout.count()):
            child_layout = layout.itemAt(index).layout()
            if child_layout is not None:
                self._apply_layout_spacing(child_layout)
