import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent

from database import is_file_imported, insert_transactions, get_imported_files, file_hash, delete_file_data
from csv_importer import import_csv


class DropZone(QFrame):
    files_dropped = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setObjectName("card")
        self.setAcceptDrops(True)
        self.setMinimumHeight(160)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._set_idle_style()

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(8)

        icon = QLabel("📂")
        icon.setFont(QFont("Segoe UI Emoji", 36))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("background: transparent;")

        hint = QLabel("Przeciągnij plik CSV z mBanku tutaj\nlub kliknij przycisk poniżej")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: #718096; font-size: 14px; background: transparent;")

        lay.addWidget(icon)
        lay.addWidget(hint)

    def _set_idle_style(self):
        self.setStyleSheet(
            "QFrame#card { border: 2px dashed #CBD5E0; border-radius: 10px;"
            " background-color: #FAFBFC; }"
        )

    def _set_hover_style(self):
        self.setStyleSheet(
            "QFrame#card { border: 2px dashed #4A90D9; border-radius: 10px;"
            " background-color: #EBF4FF; }"
        )

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._set_hover_style()

    def dragLeaveEvent(self, event):
        self._set_idle_style()

    def dropEvent(self, event: QDropEvent):
        self._set_idle_style()
        csvs = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.toLocalFile().lower().endswith(".csv")
        ]
        if csvs:
            self.files_dropped.emit(csvs)


class ImportWidget(QWidget):
    data_imported = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._load_history()

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(18)

        # ── Title ─────────────────────────────────────────────────
        title = QLabel("Import CSV")
        title.setObjectName("section_title")
        lay.addWidget(title)

        # ── Drop zone ─────────────────────────────────────────────
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self._do_import)
        lay.addWidget(self.drop_zone)

        # ── Browse button ─────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        browse_btn = QPushButton("📁   Wybierz plik(i) CSV")
        browse_btn.setObjectName("primary_button")
        browse_btn.setFont(QFont("Segoe UI", 13))
        browse_btn.setMinimumWidth(220)
        browse_btn.clicked.connect(self._browse)
        btn_row.addWidget(browse_btn)
        lay.addLayout(btn_row)

        # ── Status label ──────────────────────────────────────────
        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setWordWrap(True)
        lay.addWidget(self.status_lbl)

        # ── History table ─────────────────────────────────────────
        hist_frame = QFrame()
        hist_frame.setObjectName("card")
        hist_frame.setFrameShape(QFrame.Shape.StyledPanel)
        hist_vbox = QVBoxLayout(hist_frame)
        hist_vbox.setContentsMargins(16, 14, 16, 14)
        hist_vbox.setSpacing(10)

        hist_hdr = QHBoxLayout()
        hist_title = QLabel("Historia importów")
        hist_title.setObjectName("card_section_title")
        hist_hdr.addWidget(hist_title)
        hist_hdr.addStretch()

        del_btn = QPushButton("🗑  Usuń zaznaczony")
        del_btn.setObjectName("danger_button")
        del_btn.clicked.connect(self._delete_selected)
        hist_hdr.addWidget(del_btn)
        hist_vbox.addLayout(hist_hdr)

        self.hist_table = QTableWidget()
        self.hist_table.setColumnCount(5)
        self.hist_table.setHorizontalHeaderLabels(
            ["Plik", "Okres od", "Okres do", "Transakcji", "Zaimportowano"]
        )
        hh = self.hist_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.hist_table.verticalHeader().setVisible(False)
        self.hist_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.hist_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.hist_table.setAlternatingRowColors(True)
        self.hist_table.setMinimumHeight(180)
        hist_vbox.addWidget(self.hist_table)

        lay.addWidget(hist_frame)
        lay.addStretch()

    # ── Public ─────────────────────────────────────────────────────────────────

    # ── Private ────────────────────────────────────────────────────────────────

    def _browse(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Wybierz pliki CSV z mBanku",
            os.path.expanduser("~\\Downloads"), "CSV (*.csv)"
        )
        if files:
            self._do_import(files)

    def _do_import(self, files: list):
        imported = skipped = errors = 0

        for path in files:
            try:
                h = file_hash(path)
                if is_file_imported(h):
                    skipped += 1
                    continue
                txns = import_csv(path)
                if not txns:
                    errors += 1
                    continue
                insert_transactions(txns, os.path.basename(path), h)
                imported += 1
            except Exception as exc:
                errors += 1
                QMessageBox.warning(
                    self, "Błąd importu",
                    f"Nie udało się zaimportować:\n{os.path.basename(path)}\n\n{exc}",
                )

        parts = []
        if imported:
            parts.append(f"✅ Zaimportowano: {imported} plik(ów)")
        if skipped:
            parts.append(f"⏭ Pominięto (duplikat): {skipped}")
        if errors:
            parts.append(f"❌ Błędy: {errors}")

        if parts:
            color = "#38A169" if not errors else "#E53E3E"
            self.status_lbl.setText("  |  ".join(parts))
            self.status_lbl.setStyleSheet(f"font-size: 13px; color: {color};")

        if imported:
            self._load_history()
            self.data_imported.emit()

    def _load_history(self):
        files = get_imported_files()
        self.hist_table.setRowCount(len(files))
        for row, f in enumerate(files):
            self.hist_table.setItem(row, 0, QTableWidgetItem(f["filename"] or ""))
            self.hist_table.setItem(row, 1, QTableWidgetItem(f["period_start"] or ""))
            self.hist_table.setItem(row, 2, QTableWidgetItem(f["period_end"] or ""))
            self.hist_table.setItem(row, 3, QTableWidgetItem(str(f["transaction_count"])))
            ts = (f["imported_at"] or "")[:16].replace("T", " ")
            item = QTableWidgetItem(ts)
            item.setData(Qt.ItemDataRole.UserRole, f["file_hash"])
            self.hist_table.setItem(row, 4, item)

    def _delete_selected(self):
        row = self.hist_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Brak zaznaczenia", "Zaznacz wiersz do usunięcia.")
            return
        hash_item = self.hist_table.item(row, 4)
        if not hash_item:
            return
        fname = self.hist_table.item(row, 0)
        name = fname.text() if fname else "ten plik"
        reply = QMessageBox.question(
            self, "Usuń import",
            f"Czy na pewno chcesz usunąć dane z:\n{name}?\n\nWszystkie powiązane transakcje zostaną skasowane.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_file_data(hash_item.data(Qt.ItemDataRole.UserRole))
            self._load_history()
            self.data_imported.emit()
            self.status_lbl.setText("🗑 Import usunięty.")
            self.status_lbl.setStyleSheet("font-size: 13px; color: #E53E3E;")
