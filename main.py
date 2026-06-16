from app.utils.logging_config import configure_error_logging
from app.startup import StartupController


def create_application(argv: list[str]):
    from PyQt6.QtWidgets import QApplication

    return QApplication(argv)


def main() -> None:
    configure_error_logging()
    import sys

    application = create_application(sys.argv)
    controller = StartupController()
    controller.show_initial_window()
    sys.exit(application.exec())


if __name__ == "__main__":
    main()
