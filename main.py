import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from database import initialize_db
from ui.main_window import MainWindow
from ui.styles import MAIN_STYLE


def main():
    initialize_db()

    app = QApplication(sys.argv)
    app.setApplicationName("mBank Expense Tracker")
    app.setStyleSheet(MAIN_STYLE)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
