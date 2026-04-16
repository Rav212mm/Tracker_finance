from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.dashboard_widget import DashboardWidget
from ui.transactions_widget import TransactionsWidget
from ui.import_widget import ImportWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("mBank Expense Tracker")
        self.setMinimumSize(1200, 720)
        self.resize(1440, 860)
        self._setup_ui()

    def _setup_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.stack.setObjectName("content_area")

        self.dashboard = DashboardWidget()
        self.transactions = TransactionsWidget()
        self.import_widget = ImportWidget()
        self.import_widget.data_imported.connect(self._on_data_imported)

        self.stack.addWidget(self.dashboard)      # 0
        self.stack.addWidget(self.transactions)   # 1
        self.stack.addWidget(self.import_widget)  # 2

        layout.addWidget(self.stack)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)

        vbox = QVBoxLayout(sidebar)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        # ── Logo area ──────────────────────────────────────────────
        logo_area = QWidget()
        logo_area.setStyleSheet("background-color: #152138; padding: 0;")
        logo_vbox = QVBoxLayout(logo_area)
        logo_vbox.setContentsMargins(20, 24, 20, 20)
        logo_vbox.setSpacing(3)

        icon_lbl = QLabel("💳")
        icon_lbl.setFont(QFont("Segoe UI Emoji", 30))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("color: white; background: transparent;")

        title_lbl = QLabel("Expense Tracker")
        title_lbl.setObjectName("app_title")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub_lbl = QLabel("mBank CSV")
        sub_lbl.setObjectName("app_subtitle")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_vbox.addWidget(icon_lbl)
        logo_vbox.addWidget(title_lbl)
        logo_vbox.addWidget(sub_lbl)
        vbox.addWidget(logo_area)

        # ── Divider ────────────────────────────────────────────────
        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #2D4470;")
        vbox.addWidget(divider)
        vbox.addSpacing(8)

        # ── Nav buttons ────────────────────────────────────────────
        self._nav_buttons: list[QPushButton] = []
        nav_items = [
            ("📊   Dashboard", 0),
            ("📋   Transakcje", 1),
            ("📥   Import CSV", 2),
        ]
        for label, idx in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("nav_button")
            btn.setCheckable(True)
            btn.setFont(QFont("Segoe UI", 12))
            btn.clicked.connect(lambda _checked, i=idx: self._navigate(i))
            self._nav_buttons.append(btn)
            vbox.addWidget(btn)

        self._nav_buttons[0].setChecked(True)

        vbox.addStretch()

        version_lbl = QLabel("v1.0")
        version_lbl.setStyleSheet("color: #A8C4E8; padding: 10px; font-size: 11px;")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(version_lbl)

        return sidebar

    def _navigate(self, index: int):
        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == index)
        self.stack.setCurrentIndex(index)

    def _on_data_imported(self):
        self.dashboard.refresh()
        self.transactions.refresh()
