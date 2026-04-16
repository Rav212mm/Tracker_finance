from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QFrame, QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from database import (
    get_months, get_summary,
    get_expenses_by_category, get_monthly_expenses,
)
from analytics import get_reducible_insights
from ui.styles import fmt_pln

# ── Category colours ──────────────────────────────────────────────────────────
CAT_COLORS: dict[str, str] = {
    "Żywność i chemia domowa": "#48BB78",
    "Paliwo":                  "#4299E1",
    "Sport i hobby":           "#ED8936",
    "Zdrowie i uroda":         "#ED64A6",
    "Czynsz i wynajem":        "#9F7AEA",
    "Opłaty i odsetki":        "#FC8181",
    "Multimedia, książki i prasa": "#38B2AC",
    "Spłaty rat":              "#A0522D",
    "Podatki":                 "#718096",
    "Bez kategorii":           "#A0AEC0",
    "Wypłata gotówki":         "#F6AD55",
    "Remont i ogród":          "#68D391",
    "Osobiste - inne":         "#F6E05E",
    "Rozrywka":                "#B794F4",
    "Wpływy - inne":           "#4FD1C5",
}
DEFAULT_COLOR = "#CBD5E0"

MONTH_NAMES = [
    "", "Sty", "Lut", "Mar", "Kwi", "Maj", "Cze",
    "Lip", "Sie", "Wrz", "Paź", "Lis", "Gru",
]
MONTH_NAMES_FULL = [
    "", "Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec",
    "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień",
]


# ── Helper widgets ─────────────────────────────────────────────────────────────

class SummaryCard(QFrame):
    def __init__(self, label: str, value: str = "—", color: str = "#1C2B4A"):
        super().__init__()
        self.setObjectName("card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(96)

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(18, 14, 18, 14)
        vbox.setSpacing(4)

        self._label = QLabel(label)
        self._label.setStyleSheet("color: #4A5568; font-size: 12px;")

        self._value = QLabel(value)
        self._value.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self._value.setStyleSheet(f"color: {color};")

        vbox.addWidget(self._label)
        vbox.addWidget(self._value)

    def update(self, value: str, color: str = None):  # type: ignore[override]
        self._value.setText(value)
        if color:
            self._value.setStyleSheet(f"color: {color};")


class ChartFrame(QWidget):
    def __init__(self, figsize=(6, 4)):
        super().__init__()
        self.fig = Figure(figsize=figsize, facecolor="white")
        self.canvas = FigureCanvasQTAgg(self.fig)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.canvas)

    def clear(self):
        self.fig.clear()

    def draw(self):
        self.canvas.draw()


class InsightRow(QFrame):
    def __init__(self, category: str, total: float, trend_pct: float | None, ctype: str):
        super().__init__()
        self.setObjectName("card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "QFrame#card { border: 1px solid #EDF2F7; border-radius: 6px; }"
        )

        hbox = QHBoxLayout(self)
        hbox.setContentsMargins(10, 8, 10, 8)
        hbox.setSpacing(8)

        dot_color = "#C53030" if ctype == "discretionary" else "#92400E"
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {dot_color}; font-size: 14px;")
        dot.setFixedWidth(18)

        cat_lbl = QLabel(category)
        cat_lbl.setFont(QFont("Segoe UI", 11))
        cat_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        amt_lbl = QLabel(fmt_pln(total))
        amt_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        amt_lbl.setStyleSheet("color: #C53030;")

        hbox.addWidget(dot)
        hbox.addWidget(cat_lbl)
        hbox.addWidget(amt_lbl)

        if trend_pct is not None:
            if trend_pct > 5:
                txt, col = f"↑{trend_pct:.0f}%", "#C53030"
            elif trend_pct < -5:
                txt, col = f"↓{abs(trend_pct):.0f}%", "#276749"
            else:
                txt, col = "→", "#4A5568"
            trend_lbl = QLabel(txt)
            trend_lbl.setStyleSheet(f"color: {col}; font-size: 11px; font-weight: bold;")
            trend_lbl.setFixedWidth(44)
            trend_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            hbox.addWidget(trend_lbl)


# ── Main dashboard ─────────────────────────────────────────────────────────────

class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(28, 24, 28, 28)
        lay.setSpacing(18)

        # ── Header ────────────────────────────────────────────────
        hdr = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setObjectName("section_title")
        hdr.addWidget(title)
        hdr.addStretch()

        period_lbl = QLabel("Okres:")
        period_lbl.setStyleSheet("color: #2D3748;")
        self.month_combo = QComboBox()
        self.month_combo.setMinimumWidth(180)
        self.month_combo.currentIndexChanged.connect(lambda: self.refresh(update_months=False))

        hdr.addWidget(period_lbl)
        hdr.addWidget(self.month_combo)
        lay.addLayout(hdr)

        # ── Summary cards ─────────────────────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)
        self.card_exp   = SummaryCard("Wydatki",     "—", "#E53E3E")
        self.card_inc   = SummaryCard("Wpływy",      "—", "#38A169")
        self.card_bal   = SummaryCard("Bilans",      "—", "#1C2B4A")
        self.card_count = SummaryCard("Transakcji",  "—", "#3182CE")
        for c in (self.card_exp, self.card_inc, self.card_bal, self.card_count):
            cards_row.addWidget(c)
        lay.addLayout(cards_row)

        # ── Middle row: category chart + insights ─────────────────
        mid = QHBoxLayout()
        mid.setSpacing(18)

        # Category bar chart
        cat_frame = QFrame()
        cat_frame.setObjectName("card")
        cat_frame.setFrameShape(QFrame.Shape.StyledPanel)
        cat_vbox = QVBoxLayout(cat_frame)
        cat_vbox.setContentsMargins(16, 14, 16, 14)

        cat_title = QLabel("Wydatki wg kategorii")
        cat_title.setObjectName("card_section_title")
        self.cat_chart = ChartFrame(figsize=(6, 5))

        cat_vbox.addWidget(cat_title)
        cat_vbox.addWidget(self.cat_chart)
        mid.addWidget(cat_frame, stretch=3)

        # Insights panel
        ins_frame = QFrame()
        ins_frame.setObjectName("card")
        ins_frame.setFrameShape(QFrame.Shape.StyledPanel)
        ins_vbox = QVBoxLayout(ins_frame)
        ins_vbox.setContentsMargins(16, 14, 16, 14)
        ins_vbox.setSpacing(8)

        ins_title = QLabel("🎯 Gdzie możesz zaoszczędzić")
        ins_title.setObjectName("card_section_title")
        ins_hint = QLabel("Wydatki uznaniowe i optymalizowalne")
        ins_hint.setStyleSheet("color: #4A5568; font-size: 11px;")

        ins_vbox.addWidget(ins_title)
        ins_vbox.addWidget(ins_hint)

        ins_scroll = QScrollArea()
        ins_scroll.setWidgetResizable(True)
        ins_scroll.setFrameShape(QFrame.Shape.NoFrame)
        ins_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.ins_container = QWidget()
        self.ins_layout = QVBoxLayout(self.ins_container)
        self.ins_layout.setContentsMargins(0, 0, 0, 0)
        self.ins_layout.setSpacing(5)

        ins_scroll.setWidget(self.ins_container)
        ins_vbox.addWidget(ins_scroll)
        mid.addWidget(ins_frame, stretch=2)

        lay.addLayout(mid)

        # ── Monthly trend ─────────────────────────────────────────
        trend_frame = QFrame()
        trend_frame.setObjectName("card")
        trend_frame.setFrameShape(QFrame.Shape.StyledPanel)
        trend_vbox = QVBoxLayout(trend_frame)
        trend_vbox.setContentsMargins(16, 14, 16, 14)

        trend_title = QLabel("Trend miesięczny wydatków")
        trend_title.setObjectName("card_section_title")
        self.trend_chart = ChartFrame(figsize=(12, 3))

        trend_vbox.addWidget(trend_title)
        trend_vbox.addWidget(self.trend_chart)
        lay.addWidget(trend_frame)

        scroll.setWidget(content)
        outer.addWidget(scroll)

    # ── Public API ─────────────────────────────────────────────────────────────

    def refresh(self, update_months: bool = True):
        if update_months:
            self._populate_months()
        ym = self.month_combo.currentData()
        self._update_cards(ym)
        self._update_cat_chart(ym)
        self._update_insights(ym)
        self._update_trend_chart()

    # ── Private helpers ────────────────────────────────────────────────────────

    def _populate_months(self):
        self.month_combo.blockSignals(True)
        prev = self.month_combo.currentData()
        self.month_combo.clear()
        self.month_combo.addItem("Wszystkie okresy", None)

        months = get_months()
        for ym in months:
            y, m = ym.split("-")
            self.month_combo.addItem(f"{MONTH_NAMES_FULL[int(m)]} {y}", ym)

        if prev:
            idx = self.month_combo.findData(prev)
            if idx >= 0:
                self.month_combo.setCurrentIndex(idx)
                self.month_combo.blockSignals(False)
                return
        if months:
            self.month_combo.setCurrentIndex(1)  # most recent
        self.month_combo.blockSignals(False)

    def _update_cards(self, ym: str | None):
        s = get_summary(ym, exclude_internal=True)
        exp = s["total_expenses"]
        inc = s["total_income"]
        bal = inc - exp

        self.card_exp.update(fmt_pln(exp), "#E53E3E")
        self.card_inc.update(fmt_pln(inc), "#38A169")
        bal_color = "#38A169" if bal >= 0 else "#E53E3E"
        sign = "+" if bal >= 0 else ""
        self.card_bal.update(f"{sign}{fmt_pln(bal)}", bal_color)
        self.card_count.update(str(s["transaction_count"]), "#3182CE")

    def _update_cat_chart(self, ym: str | None):
        cats = get_expenses_by_category(ym, exclude_internal=True)
        self.cat_chart.clear()
        ax = self.cat_chart.fig.add_subplot(111)
        ax.set_facecolor("#FAFBFC")

        if not cats:
            ax.text(0.5, 0.5, "Brak danych", ha="center", va="center",
                    fontsize=13, color="#A0AEC0")
            ax.axis("off")
            self.cat_chart.draw()
            return

        # Top 9, rest → "Inne"
        if len(cats) > 9:
            top = cats[:9]
            rest = sum(c["total"] for c in cats[9:])
            if rest > 0:
                top.append({"category": "Inne", "total": rest})
            cats = top

        labels = [c["category"] for c in cats]
        values = [c["total"] for c in cats]
        colors = [CAT_COLORS.get(lbl, DEFAULT_COLOR) for lbl in labels]
        max_v = max(values) if values else 1

        bars = ax.barh(range(len(labels)), values, color=colors, height=0.6, zorder=2)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=10)
        ax.invert_yaxis()
        ax.set_xlabel("PLN", fontsize=9, color="#718096")
        ax.tick_params(colors="#4A5568")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_color("#E2E8F0")
        ax.xaxis.grid(True, color="#EDF2F7", zorder=0)
        ax.set_axisbelow(True)

        for bar, val in zip(bars, values):
            ax.text(
                bar.get_width() + max_v * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{val:,.0f}".replace(",", "\u00a0"),
                va="center", fontsize=9, color="#4A5568",
            )
        ax.set_xlim(0, max_v * 1.22)
        self.cat_chart.fig.tight_layout()
        self.cat_chart.draw()

    def _update_insights(self, ym: str | None):
        # Clear
        while self.ins_layout.count():
            item = self.ins_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        insights = get_reducible_insights(ym)

        if not insights:
            lbl = QLabel("Brak danych.\nZaimportuj plik CSV.")
            lbl.setStyleSheet("color: #4A5568; padding: 20px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ins_layout.addWidget(lbl)
            self.ins_layout.addStretch()
            return

        total = sum(i["total"] for i in insights)
        potential = total * 0.20

        summary = QLabel(
            f"Suma wydatków do redukcji: <b>{fmt_pln(total)}</b><br>"
            f"Potencjalna oszczędność (−20%): <b style='color:#276749'>{fmt_pln(potential)}</b>"
        )
        summary.setTextFormat(Qt.TextFormat.RichText)
        summary.setStyleSheet(
            "background:#C6F6D5; color:#1C4532; padding:10px; "
            "border-radius:6px; font-size:12px;"
        )
        summary.setWordWrap(True)
        self.ins_layout.addWidget(summary)

        for ins in insights[:10]:
            self.ins_layout.addWidget(
                InsightRow(ins["category"], ins["total"], ins.get("trend_pct"), ins["type"])
            )
        self.ins_layout.addStretch()

    def _update_trend_chart(self):
        monthly = get_monthly_expenses()
        self.trend_chart.clear()
        ax = self.trend_chart.fig.add_subplot(111)
        ax.set_facecolor("#FAFBFC")

        if not monthly:
            ax.text(0.5, 0.5, "Brak danych o trendzie — zaimportuj więcej miesięcy",
                    ha="center", va="center", fontsize=12, color="#A0AEC0")
            ax.axis("off")
            self.trend_chart.draw()
            return

        months = [m["month"] for m in monthly]
        values = [m["total"] for m in monthly]
        labels = []
        for ym in months:
            y, m = ym.split("-")
            labels.append(f"{MONTH_NAMES[int(m)]}\n{y}")

        max_v = max(values) if values else 1
        bar_colors = ["#4A90D9"] * len(values)
        # Highlight the most expensive month
        if values:
            bar_colors[values.index(max(values))] = "#FC8181"

        bars = ax.bar(range(len(labels)), values, color=bar_colors, width=0.55, zorder=2)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=10, color="#4A5568")
        ax.set_ylabel("PLN", fontsize=9, color="#718096")
        ax.tick_params(axis="y", colors="#4A5568")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#E2E8F0")
        ax.spines["bottom"].set_color("#E2E8F0")
        ax.yaxis.grid(True, color="#EDF2F7", zorder=0)
        ax.set_axisbelow(True)

        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max_v * 0.015,
                f"{val:,.0f}".replace(",", "\u00a0"),
                ha="center", va="bottom", fontsize=9, color="#4A5568",
            )
        ax.set_ylim(0, max_v * 1.18)

        if len(values) > 1:
            avg = sum(values) / len(values)
            ax.axhline(avg, color="#FC8181", linestyle="--", linewidth=1.4, alpha=0.8)
            ax.text(
                len(labels) - 0.5, avg + max_v * 0.025,
                f"Śr: {avg:,.0f}".replace(",", "\u00a0"),
                ha="right", fontsize=9, color="#E53E3E",
            )

        self.trend_chart.fig.tight_layout()
        self.trend_chart.draw()
