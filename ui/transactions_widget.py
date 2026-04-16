from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QPushButton,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from database import get_transactions, get_months
from ui.styles import fmt_pln

MONTH_NAMES_FULL = [
    "", "Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec",
    "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień",
]


class _AmountItem(QTableWidgetItem):
    """Table item that sorts numerically."""
    def __lt__(self, other: QTableWidgetItem) -> bool:
        try:
            return float(self.data(Qt.ItemDataRole.UserRole)) < float(
                other.data(Qt.ItemDataRole.UserRole)
            )
        except (TypeError, ValueError):
            return super().__lt__(other)


class TransactionsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(16)

        # ── Header ────────────────────────────────────────────────
        title = QLabel("Transakcje")
        title.setObjectName("section_title")
        lay.addWidget(title)

        # ── Filters bar ───────────────────────────────────────────
        fbar = QFrame()
        fbar.setObjectName("card")
        fbar.setFrameShape(QFrame.Shape.StyledPanel)
        fhbox = QHBoxLayout(fbar)
        fhbox.setContentsMargins(16, 10, 16, 10)
        fhbox.setSpacing(12)

        fhbox.addWidget(QLabel("Miesiąc:"))
        self.month_combo = QComboBox()
        self.month_combo.addItem("Wszystkie", None)
        self.month_combo.currentIndexChanged.connect(self._load)
        fhbox.addWidget(self.month_combo)

        fhbox.addWidget(QLabel("Kategoria:"))
        self.cat_combo = QComboBox()
        self.cat_combo.addItem("Wszystkie", None)
        self.cat_combo.setMinimumWidth(190)
        self.cat_combo.currentIndexChanged.connect(self._load)
        fhbox.addWidget(self.cat_combo)

        fhbox.addWidget(QLabel("Szukaj:"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Opis, sklep…")
        self.search.setMinimumWidth(200)
        self.search.textChanged.connect(self._load)
        fhbox.addWidget(self.search)

        fhbox.addStretch()

        self.only_exp_btn = QPushButton("Tylko wydatki")
        self.only_exp_btn.setObjectName("primary_button")
        self.only_exp_btn.setCheckable(True)
        self.only_exp_btn.toggled.connect(self._load)
        fhbox.addWidget(self.only_exp_btn)

        self.hide_int_btn = QPushButton("Ukryj transfery wewnętrzne")
        self.hide_int_btn.setObjectName("primary_button")
        self.hide_int_btn.setCheckable(True)
        self.hide_int_btn.setChecked(True)
        self.hide_int_btn.toggled.connect(self._load)
        fhbox.addWidget(self.hide_int_btn)

        lay.addWidget(fbar)

        # ── Table ─────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Data", "Opis", "Kategoria", "Rachunek", "Kwota"])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        lay.addWidget(self.table)

        # ── Footer ────────────────────────────────────────────────
        self.footer = QLabel("Transakcji: 0   |   Suma wydatków: 0,00 zł")
        self.footer.setStyleSheet("color: #718096; font-size: 12px;")
        lay.addWidget(self.footer)

    # ── Public API ─────────────────────────────────────────────────────────────

    def refresh(self):
        self._populate_months()
        self._populate_categories()
        self._load()

    # ── Private ────────────────────────────────────────────────────────────────

    def _populate_months(self):
        prev = self.month_combo.currentData()
        self.month_combo.blockSignals(True)
        self.month_combo.clear()
        self.month_combo.addItem("Wszystkie", None)
        for ym in get_months():
            y, m = ym.split("-")
            self.month_combo.addItem(f"{MONTH_NAMES_FULL[int(m)]} {y}", ym)
        if prev:
            idx = self.month_combo.findData(prev)
            if idx >= 0:
                self.month_combo.setCurrentIndex(idx)
        self.month_combo.blockSignals(False)

    def _populate_categories(self):
        prev = self.cat_combo.currentData()
        self.cat_combo.blockSignals(True)
        self.cat_combo.clear()
        self.cat_combo.addItem("Wszystkie", None)
        rows = get_transactions()
        cats = sorted({r["category"] for r in rows if r["category"]})
        for c in cats:
            self.cat_combo.addItem(c, c)
        if prev:
            idx = self.cat_combo.findData(prev)
            if idx >= 0:
                self.cat_combo.setCurrentIndex(idx)
        self.cat_combo.blockSignals(False)

    def _load(self):
        ym = self.month_combo.currentData()
        cat = self.cat_combo.currentData()
        search = self.search.text().strip() or None
        exclude_int = self.hide_int_btn.isChecked()

        rows = get_transactions(ym, cat, search, exclude_internal=exclude_int)

        if self.only_exp_btn.isChecked():
            rows = [r for r in rows if r["amount"] < 0]

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))

        total_exp = 0.0
        for i, r in enumerate(rows):
            amount = r["amount"]
            if amount < 0:
                total_exp += abs(amount)

            date_item = QTableWidgetItem(r["date"])
            desc_item = QTableWidgetItem(r["description"])
            cat_item  = QTableWidgetItem(r["category"])
            acc_item  = QTableWidgetItem(r["account"])

            amt_item = _AmountItem(fmt_pln(amount, show_sign=True))
            amt_item.setData(Qt.ItemDataRole.UserRole, amount)
            amt_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            if amount < 0:
                amt_item.setForeground(QColor("#E53E3E"))
            else:
                amt_item.setForeground(QColor("#38A169"))

            if r.get("is_internal"):
                for item in (date_item, desc_item, cat_item, acc_item, amt_item):
                    item.setForeground(QColor("#A0AEC0"))

            self.table.setItem(i, 0, date_item)
            self.table.setItem(i, 1, desc_item)
            self.table.setItem(i, 2, cat_item)
            self.table.setItem(i, 3, acc_item)
            self.table.setItem(i, 4, amt_item)

        self.table.setSortingEnabled(True)
        self.footer.setText(
            f"Transakcji: {len(rows)}   |   Suma wydatków: {fmt_pln(total_exp)}"
        )
