MAIN_STYLE = """
/* ── Global ── */
QWidget {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
    color: #1A202C;
}

QLabel {
    color: #1A202C;
}

QMainWindow, QWidget#content_area {
    background-color: #F0F2F5;
}

/* ── Sidebar ── */
QWidget#sidebar {
    background-color: #1C2B4A;
}

QLabel#app_title {
    color: #FFFFFF;
    font-size: 15px;
    font-weight: bold;
}

QLabel#app_subtitle {
    color: #B8D0F0;
    font-size: 11px;
}

QPushButton#nav_button {
    color: #B0C4DE;
    background-color: transparent;
    border: none;
    border-left: 3px solid transparent;
    padding: 13px 20px 13px 17px;
    text-align: left;
    font-size: 13px;
}

QPushButton#nav_button:hover {
    background-color: #243552;
    color: #FFFFFF;
}

QPushButton#nav_button:checked {
    background-color: #2D4470;
    color: #FFFFFF;
    border-left: 3px solid #4A90D9;
    font-weight: bold;
}

/* ── Section titles ── */
QLabel#section_title {
    font-size: 22px;
    font-weight: bold;
    color: #1C2B4A;
}

QLabel#card_section_title {
    font-size: 14px;
    font-weight: bold;
    color: #1C2B4A;
}

/* ── Cards ── */
QFrame#card {
    background-color: #FFFFFF;
    border-radius: 10px;
    border: 1px solid #E2E8F0;
}

/* ── Combo boxes ── */
QComboBox {
    padding: 6px 10px;
    border: 1px solid #CBD5E0;
    border-radius: 6px;
    background-color: #FFFFFF;
    color: #1A202C;
    min-width: 160px;
}

QComboBox:focus {
    border: 2px solid #4A90D9;
}

QComboBox::drop-down {
    border: none;
    padding-right: 6px;
}

QComboBox QAbstractItemView {
    border: 1px solid #CBD5E0;
    border-radius: 4px;
    background-color: #FFFFFF;
    color: #1A202C;
    selection-background-color: #EBF4FF;
    selection-color: #1C2B4A;
}

/* ── Buttons ── */
QPushButton#primary_button {
    background-color: #1C2B4A;
    color: #FFFFFF;
    border: none;
    padding: 9px 20px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: bold;
}

QPushButton#primary_button:hover {
    background-color: #2D4470;
}

QPushButton#primary_button:pressed {
    background-color: #152138;
}

QPushButton#primary_button:checked {
    background-color: #4A90D9;
}

QPushButton#danger_button {
    background-color: #E53E3E;
    color: #FFFFFF;
    border: none;
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 12px;
}

QPushButton#danger_button:hover {
    background-color: #C53030;
}

/* ── Line edits ── */
QLineEdit {
    padding: 7px 11px;
    border: 1px solid #CBD5E0;
    border-radius: 6px;
    background-color: #FFFFFF;
    color: #1A202C;
}

QLineEdit:focus {
    border: 2px solid #4A90D9;
}

/* ── Tables ── */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 6px;
    gridline-color: #F7FAFC;
    alternate-background-color: #F7FAFC;
}

QTableWidget::item {
    padding: 7px 10px;
    color: #1A202C;
}

QTableWidget::item:selected {
    background-color: #EBF4FF;
    color: #1C2B4A;
}

QHeaderView::section {
    background-color: #EDF2F7;
    color: #4A5568;
    padding: 8px 10px;
    border: none;
    border-right: 1px solid #E2E8F0;
    border-bottom: 1px solid #CBD5E0;
    font-weight: bold;
    font-size: 12px;
}

QHeaderView::section:first {
    border-top-left-radius: 6px;
}

QHeaderView::section:last {
    border-top-right-radius: 6px;
    border-right: none;
}

/* ── Scroll bars ── */
QScrollBar:vertical {
    border: none;
    background: #F0F2F5;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #CBD5E0;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #A0AEC0;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    border: none;
    background: #F0F2F5;
    height: 8px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: #CBD5E0;
    border-radius: 4px;
}

/* ── Tooltips ── */
QToolTip {
    background-color: #1C2B4A;
    color: #FFFFFF;
    border: none;
    padding: 5px 8px;
    border-radius: 4px;
}

/* ── Message boxes ── */
QMessageBox {
    background-color: #FFFFFF;
}
"""


def fmt_pln(amount: float, show_sign: bool = False) -> str:
    """Format a float as Polish currency string: 1 542,90 zł"""
    s = f"{abs(amount):,.2f}"
    # Python uses comma as thousands sep and period as decimal
    # We need space as thousands and comma as decimal
    s = s.replace(".", "|").replace(",", "\u00a0").replace("|", ",")
    if show_sign:
        sign = "+" if amount >= 0 else "-"
        return f"{sign}{s} zł"
    return f"{s} zł"
