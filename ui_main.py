from __future__ import annotations

import calendar
from datetime import date, timedelta
from urllib.parse import urlparse

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from export import export_csv, export_month_png
from models import Event, EventStatus

STATUS_ORDER = [
    EventStatus.CONFIRMED,
    EventStatus.OFFICIAL,
    EventStatus.EXPECTED,
    EventStatus.UNSURE,
    EventStatus.UNKNOWN,
]

STATUS_PRIORITY = {
    EventStatus.CONFIRMED: 0,
    EventStatus.OFFICIAL: 1,
    EventStatus.EXPECTED: 2,
    EventStatus.UNSURE: 3,
    EventStatus.UNKNOWN: 4,
}

PLATFORM_ICON = {
    "PC": "🖥️",
    "WIN": "🪟",
    "PS5": "🎮",
    "PS4": "🎮",
    "XSX": "🟩",
    "XBO": "🟩",
    "XSX|S": "🟩",
    "NS": "🟥",
    "NS2": "🟥",
}


class DayCell(QFrame):
    clicked = Signal(date)

    def __init__(self) -> None:
        super().__init__()
        self.day: date | None = None
        self.setObjectName("DayCell")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(96)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(4)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)

        self.day_label = QLabel("")
        self.day_label.setObjectName("DayNumber")

        self.extra_badge = QLabel("")
        self.extra_badge.setObjectName("CountBadge")
        self.extra_badge.hide()
        self.link_badge = QLabel("")
        self.link_badge.setObjectName("LinkBadge")
        self.link_badge.hide()

        top.addWidget(self.day_label)
        top.addStretch(1)
        top.addWidget(self.link_badge)
        top.addWidget(self.extra_badge)
        root.addLayout(top)

        self.preview_box = QVBoxLayout()
        self.preview_box.setContentsMargins(0, 0, 0, 0)
        self.preview_box.setSpacing(3)
        root.addLayout(self.preview_box)
        root.addStretch(1)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton and self.day:
            self.clicked.emit(self.day)
        super().mousePressEvent(event)

    def set_data(self, day: date, in_month: bool, is_today: bool, is_selected: bool, events_on_day: list[Event]) -> None:
        self.day = day
        self.day_label.setText(str(day.day))
        self.setProperty("outside", not in_month)
        self.setProperty("today", is_today)
        self.setProperty("selected", is_selected)
        self._repolish()

        while self.preview_box.count():
            item = self.preview_box.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        previews = events_on_day[:2]
        for ev in previews:
            lead_emoji = f"{ev.emoji_tags[0]} " if ev.emoji_tags else ""
            pill_text = f"{lead_emoji}{ev.title}"
            pill = QLabel(pill_text[:22])
            pill.setObjectName("EventPill")
            pill.setProperty("status", ev.status.name.lower())
            pill.setToolTip(f"{pill_text}\n{ev.date_range_str()} | {ev.status.value}")
            pill.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self.preview_box.addWidget(pill)

        if events_on_day:
            top_status = sorted(events_on_day, key=lambda x: STATUS_PRIORITY.get(x.status, 99))[0].status
            self.extra_badge.setProperty("status", top_status.name.lower())
            url_count = sum(1 for ev in events_on_day if ev.url)
            if url_count > 0:
                self.link_badge.setText("🔗" if url_count == 1 else f"🔗{url_count}")
                self.link_badge.setToolTip(f"링크 포함 일정 {url_count}건")
                self.link_badge.show()
            else:
                self.link_badge.hide()
        else:
            self.link_badge.hide()

        if len(events_on_day) > 2:
            self.extra_badge.setText(f"+{len(events_on_day) - 2}")
            self.extra_badge.show()
        else:
            self.extra_badge.hide()

        self._repolish()

    def _repolish(self) -> None:
        style = self.style()
        style.unpolish(self)
        style.polish(self)


class GameCalendarWindow(QMainWindow):
    def __init__(
        self,
        events: list[Event],
        invalid_events: list[Event],
        source_path: str = "calendar.md",
        initial_year: int | None = None,
        initial_month: int | None = None,
        dark_mode: bool = True,
    ) -> None:
        super().__init__()
        self.events = events
        self.invalid_events = invalid_events
        self.source_path = source_path

        self.today = date.today()
        self.current_year = initial_year or self.today.year
        self.current_month = initial_month or self.today.month
        self.selected_day: date | None = None
        self.theme = "dark" if dark_mode else "light"

        self.status_filters: dict[EventStatus, QToolButton] = {}
        self.platform_filters: dict[str, QToolButton] = {}
        self.genre_filters: dict[str, QToolButton] = {}

        self.setWindowTitle("게임 캘린더")
        self.resize(1680, 940)

        self._build_ui()
        self._build_shortcuts()
        self._populate_month_controls()
        self._populate_filter_chips()
        self._apply_theme(self.theme)
        self._refresh_all()

    def _build_ui(self) -> None:
        root = QWidget(self)
        root.setObjectName("RootWidget")
        self.setCentralWidget(root)

        main = QVBoxLayout(root)
        main.setContentsMargins(16, 16, 16, 16)
        main.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(10)
        self.prev_btn = QToolButton()
        self.prev_btn.setObjectName("NavButton")
        self.prev_btn.setText("◀")
        self.next_btn = QToolButton()
        self.next_btn.setObjectName("NavButton")
        self.next_btn.setText("▶")
        self.prev_btn.setFixedSize(44, 40)
        self.next_btn.setFixedSize(44, 40)
        self.prev_btn.clicked.connect(lambda: self._move_month(-1))
        self.next_btn.clicked.connect(lambda: self._move_month(1))

        self.year_combo = QComboBox()
        self.year_combo.setObjectName("MonthCombo")
        self.month_combo = QComboBox()
        self.month_combo.setObjectName("MonthCombo")
        self.year_combo.setMinimumWidth(112)
        self.month_combo.setMinimumWidth(112)
        self.year_combo.currentIndexChanged.connect(self._on_month_combo_changed)
        self.month_combo.currentIndexChanged.connect(self._on_month_combo_changed)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("제목/태그/플랫폼/장르/상태 검색 (Ctrl+F)")
        self.search_input.setMinimumWidth(420)
        self.search_input.setMaximumWidth(700)
        self.search_input.textChanged.connect(self._refresh_all)

        self.theme_btn = QPushButton("라이트모드")
        self.theme_btn.setCheckable(True)
        self.theme_btn.setFixedHeight(40)
        self.theme_btn.clicked.connect(self._toggle_theme)

        self.btn_export_png = QPushButton("월 PNG 저장")
        self.btn_export_csv = QPushButton("CSV 내보내기")
        self.btn_export_png.setFixedHeight(40)
        self.btn_export_csv.setFixedHeight(40)
        self.btn_export_png.clicked.connect(self._on_export_png)
        self.btn_export_csv.clicked.connect(self._on_export_csv)

        header.addWidget(self.prev_btn)
        header.addWidget(self.next_btn)
        header.addWidget(self.year_combo)
        header.addWidget(self.month_combo)
        header.addStretch(1)
        header.addWidget(self.search_input, 1)
        header.addWidget(self.theme_btn)
        header.addWidget(self.btn_export_png)
        header.addWidget(self.btn_export_csv)
        main.addLayout(header)

        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("상태"))
        for status in STATUS_ORDER:
            btn = QToolButton()
            btn.setObjectName("FilterChip")
            btn.setText(status.value)
            btn.setCheckable(True)
            btn.setChecked(False)
            btn.clicked.connect(self._refresh_all)
            self.status_filters[status] = btn
            status_row.addWidget(btn)
        status_row.addStretch(1)
        main.addLayout(status_row)

        platform_row = QHBoxLayout()
        platform_row.addWidget(QLabel("플랫폼"))
        self.platform_wrap = QHBoxLayout()
        self.platform_wrap.setSpacing(6)
        platform_row.addLayout(self.platform_wrap, 1)
        main.addLayout(platform_row)

        genre_row = QHBoxLayout()
        genre_row.addWidget(QLabel("장르"))
        self.genre_wrap = QHBoxLayout()
        self.genre_wrap.setSpacing(6)
        genre_row.addLayout(self.genre_wrap, 1)
        main.addLayout(genre_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("MainSplitter")
        main.addWidget(splitter, 1)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        self.calendar_panel = QFrame()
        self.calendar_panel.setObjectName("CalendarPanel")
        panel_layout = QVBoxLayout(self.calendar_panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(8)

        self.month_title = QLabel("")
        self.month_title.setObjectName("MonthTitle")
        panel_layout.addWidget(self.month_title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)
        panel_layout.addLayout(grid)

        for col, name in enumerate(["일", "월", "화", "수", "목", "금", "토"]):
            label = QLabel(name)
            label.setObjectName("WeekHeader")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(label, 0, col)

        self.day_cells: list[DayCell] = []
        for i in range(42):
            cell = DayCell()
            cell.clicked.connect(self._on_day_clicked)
            self.day_cells.append(cell)
            grid.addWidget(cell, i // 7 + 1, i % 7)

        left_layout.addWidget(self.calendar_panel, 1)
        splitter.addWidget(left)

        right = QWidget()
        right.setObjectName("RightPane")
        right.setMinimumWidth(520)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(12, 10, 12, 10)
        right_layout.setSpacing(10)

        self.right_title = QLabel("일정")
        self.right_title.setObjectName("PanelTitle")
        right_layout.addWidget(self.right_title)

        self.events_scroll = QScrollArea()
        self.events_scroll.setObjectName("EventsPane")
        self.events_scroll.setWidgetResizable(True)
        self.events_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.events_container = QWidget()
        self.events_layout = QVBoxLayout(self.events_container)
        self.events_layout.setContentsMargins(4, 4, 4, 4)
        self.events_layout.setSpacing(12)
        self.events_layout.addStretch(1)
        self.events_scroll.setWidget(self.events_container)

        right_layout.addWidget(self.events_scroll, 1)
        splitter.addWidget(right)

        splitter.setHandleWidth(2)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([1120, 560])

    def _build_shortcuts(self) -> None:
        QShortcut(QKeySequence("Left"), self).activated.connect(lambda: self._move_month(-1))
        QShortcut(QKeySequence("Right"), self).activated.connect(lambda: self._move_month(1))
        QShortcut(QKeySequence.Find, self).activated.connect(self.search_input.setFocus)

    def _short_chip_text(self, text: str) -> str:
        if len(text) <= 8:
            return text
        return f"{text[:7]}…"

    def _populate_month_controls(self) -> None:
        years = [self.today.year - 2, self.today.year - 1, self.today.year, self.today.year + 1, self.today.year + 2]
        for event in self.events:
            if event.start_date:
                years.append(event.start_date.year)
            if event.end_date:
                years.append(event.end_date.year)

        years = sorted(set(years))

        self.year_combo.blockSignals(True)
        self.month_combo.blockSignals(True)

        self.year_combo.clear()
        self.month_combo.clear()

        for y in years:
            self.year_combo.addItem(str(y), y)

        for m in range(1, 13):
            self.month_combo.addItem(f"{m:02d}월", m)

        self.year_combo.setCurrentIndex(max(self.year_combo.findData(self.current_year), 0))
        self.month_combo.setCurrentIndex(max(self.month_combo.findData(self.current_month), 0))

        self.year_combo.blockSignals(False)
        self.month_combo.blockSignals(False)

    def _clear_layout_widgets(self, layout: QHBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _populate_filter_chips(self) -> None:
        self._clear_layout_widgets(self.platform_wrap)
        self._clear_layout_widgets(self.genre_wrap)

        self.platform_filters.clear()
        self.genre_filters.clear()

        for platform in sorted({p for e in self.events for p in e.platforms}):
            btn = QToolButton()
            btn.setObjectName("FilterChip")
            icon = PLATFORM_ICON.get(platform, "🎯")
            btn.setText(f"{icon} {platform}")
            btn.setMaximumWidth(96)
            btn.setCheckable(True)
            btn.setChecked(False)
            btn.clicked.connect(self._refresh_all)
            self.platform_filters[platform] = btn
            self.platform_wrap.addWidget(btn)
        self.platform_wrap.addStretch(1)

        for genre in sorted({g for e in self.events for g in e.genres}):
            btn = QToolButton()
            btn.setObjectName("FilterChip")
            btn.setText(self._short_chip_text(genre))
            btn.setToolTip(genre)
            btn.setMaximumWidth(104)
            btn.setCheckable(True)
            btn.setChecked(False)
            btn.clicked.connect(self._refresh_all)
            self.genre_filters[genre] = btn
            self.genre_wrap.addWidget(btn)
        self.genre_wrap.addStretch(1)

    def _apply_theme(self, theme: str) -> None:
        self.theme = theme
        root = self.centralWidget()
        root.setProperty("theme", theme)
        self.theme_btn.setChecked(theme == "dark")
        self.theme_btn.setText("라이트모드" if theme == "dark" else "다크모드")
        root.style().unpolish(root)
        root.style().polish(root)
        self._refresh_all()

    def _toggle_theme(self) -> None:
        self._apply_theme("light" if self.theme == "dark" else "dark")

    def _on_month_combo_changed(self) -> None:
        y = self.year_combo.currentData()
        m = self.month_combo.currentData()

        if isinstance(y, int):
            self.current_year = y
        if isinstance(m, int):
            self.current_month = m

        self.selected_day = None
        self._refresh_all()

    def _move_month(self, delta: int) -> None:
        base = date(self.current_year, self.current_month, 15)
        target = (base.replace(day=1) + timedelta(days=31 * delta)).replace(day=1)

        self.current_year = target.year
        self.current_month = target.month
        self.selected_day = None

        self.year_combo.blockSignals(True)
        self.month_combo.blockSignals(True)
        self.year_combo.setCurrentIndex(max(self.year_combo.findData(self.current_year), 0))
        self.month_combo.setCurrentIndex(max(self.month_combo.findData(self.current_month), 0))
        self.year_combo.blockSignals(False)
        self.month_combo.blockSignals(False)

        self._refresh_all()

    def _on_day_clicked(self, day: date) -> None:
        if self.selected_day == day:
            self.selected_day = None
            self._refresh_all()
            return

        day_events = self._events_for_calendar_day(day)
        if not day_events:
            # 빈 날짜 클릭은 월간 보기 유지
            self.selected_day = None
            self._refresh_all()
            return

        self.selected_day = day
        self._refresh_all()

    def _refresh_all(self) -> None:
        self._render_calendar()
        self._render_event_cards()

    def _events_for_calendar_day(self, day: date) -> list[Event]:
        # 달력 셀은 항상 전체 이벤트를 보여주고, 필터는 우측 리스트에만 적용한다.
        return [e for e in self.events if e.includes_date(day)]

    def _render_calendar(self) -> None:
        self.month_title.setText(f"{self.current_year}년 {self.current_month:02d}월")

        cal = calendar.Calendar(firstweekday=6)
        weeks = cal.monthdatescalendar(self.current_year, self.current_month)
        while len(weeks) < 6:
            tail = weeks[-1][-1]
            weeks.append([tail + timedelta(days=i + 1) for i in range(7)])

        day_list = [d for week in weeks[:6] for d in week]
        for cell, day in zip(self.day_cells, day_list):
            events_on_day = self._events_for_calendar_day(day)
            cell.set_data(
                day=day,
                in_month=(day.month == self.current_month),
                is_today=(day == self.today),
                is_selected=(self.selected_day == day),
                events_on_day=events_on_day,
            )

    def _render_event_cards(self) -> None:
        while self.events_layout.count() > 1:
            item = self.events_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        filtered = self._filtered_events(include_query=True)
        filtered.sort(key=lambda e: (e.start_date or date.max, STATUS_PRIORITY.get(e.status, 99), e.title.lower()))

        if self.selected_day:
            self.right_title.setText(f"일정 ({self.selected_day.isoformat()}) {len(filtered)}건")
        else:
            self.right_title.setText(f"일정 ({self.current_year}-{self.current_month:02d}) {len(filtered)}건")

        if not filtered:
            empty = QLabel("조건에 맞는 일정이 없습니다.")
            empty.setObjectName("EmptyLabel")
            self.events_layout.insertWidget(0, empty)
            return

        for event in filtered:
            self.events_layout.insertWidget(self.events_layout.count() - 1, self._build_event_card(event))

    def _build_event_card(self, event: Event) -> QWidget:
        card = QFrame()
        card.setObjectName("EventCard")
        card.setProperty("status", event.status.name.lower())

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        title_text = f"{event.emoji_tags[0]} {event.title}" if event.emoji_tags else event.title
        title = QLabel(title_text)
        title.setObjectName("EventTitle")
        title.setWordWrap(True)
        layout.addWidget(title)

        meta = QHBoxLayout()
        date_label = QLabel(event.date_range_str())
        date_label.setObjectName("EventDate")
        meta.addWidget(date_label)

        status_badge = QLabel(event.status.value)
        status_badge.setObjectName("StatusBadge")
        status_badge.setProperty("status", event.status.name.lower())
        meta.addWidget(status_badge)
        if event.url:
            domain = urlparse(event.url).netloc or event.url
            domain_label = QLabel(f"🔗 {domain}")
            domain_label.setObjectName("UrlDomain")
            domain_label.setToolTip(event.url)
            meta.addWidget(domain_label)
        meta.addStretch(1)
        layout.addLayout(meta)

        divider = QFrame()
        divider.setObjectName("CardDivider")
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Plain)
        layout.addWidget(divider)

        chips = []
        chips.extend(event.emoji_tags)
        chips.extend([f"{PLATFORM_ICON.get(p, '🎯')} {p}" for p in event.platforms])
        chips.extend([f"#{g}" for g in event.genres])
        if chips:
            chip = QLabel("  ".join(chips))
            chip.setObjectName("EventChip")
            chip.setWordWrap(True)
            layout.addWidget(chip)

        if event.description:
            desc = QLabel(event.description)
            desc.setObjectName("EventDescription")
            desc.setWordWrap(True)
            layout.addWidget(desc)

        if event.url:
            link_btn = QPushButton("링크 열기")
            link_btn.setObjectName("LinkButton")
            link_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(event.url)))
            layout.addWidget(link_btn, 0, Qt.AlignmentFlag.AlignLeft)

        return card

    def _selected_filter_values(self) -> tuple[set[EventStatus], set[str], set[str], str]:
        selected_status = {s for s, btn in self.status_filters.items() if btn.isChecked()}
        selected_platforms = {k for k, v in self.platform_filters.items() if v.isChecked()}
        selected_genres = {k for k, v in self.genre_filters.items() if v.isChecked()}
        query = self.search_input.text().strip()
        return selected_status, selected_platforms, selected_genres, query

    def _filtered_events(self, include_query: bool) -> list[Event]:
        selected_status, selected_platforms, selected_genres, query = self._selected_filter_values()

        has_platform_filter = bool(selected_platforms)
        has_genre_filter = bool(selected_genres)
        has_status_filter = bool(selected_status)

        base: list[Event] = []
        for event in self.events:
            if self.selected_day:
                if not event.includes_date(self.selected_day):
                    continue
            else:
                if not event.intersects_month(self.current_year, self.current_month):
                    continue
            base.append(event)

        out: list[Event] = []
        for event in base:
            if has_status_filter and event.status not in selected_status:
                continue

            if include_query and not event.matches_query(query):
                continue

            if has_platform_filter:
                if not event.platforms or not (set(event.platforms) & selected_platforms):
                    continue

            if has_genre_filter:
                if not event.genres or not (set(event.genres) & selected_genres):
                    continue

            out.append(event)

        return out

    def _on_export_csv(self) -> None:
        out = export_csv(self.events, self.invalid_events, "calendar_export.csv")
        QMessageBox.information(self, "완료", f"CSV 저장 완료: {out}")

    def _on_export_png(self) -> None:
        out = export_month_png(self.calendar_panel, self.current_year, self.current_month)
        QMessageBox.information(self, "완료", f"PNG 저장 완료: {out}")
