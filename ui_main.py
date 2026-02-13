from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
)

from export import export_csv, export_month_png
from models import Event


class GameCalendarWindow(QMainWindow):
    def __init__(self, events: list[Event], source_path: str = "calendar.md") -> None:
        super().__init__()
        self.events = events
        self.source_path = source_path

        self.setWindowTitle("Game Calendar")
        self.resize(980, 640)

        self.table = QTableWidget(self)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["제목", "시작일", "종료일", "상태", "태그", "플랫폼", "URL"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setCentralWidget(self.table)

        toolbar = QToolBar("내보내기", self)
        self.addToolBar(toolbar)

        btn_csv = QPushButton("CSV 내보내기", self)
        btn_csv.clicked.connect(self.on_export_csv)
        toolbar.addWidget(btn_csv)

        btn_png = QPushButton("월별 PNG 내보내기", self)
        btn_png.clicked.connect(self.on_export_png)
        toolbar.addWidget(btn_png)

        self._populate_table()

    def _populate_table(self) -> None:
        self.table.setRowCount(len(self.events))
        for r, event in enumerate(self.events):
            values = [
                event.title,
                event.start_date.isoformat() if event.start_date else "",
                event.end_date.isoformat() if event.end_date else "",
                event.status,
                ", ".join(event.tags),
                ", ".join(event.platforms),
                event.url,
            ]
            for c, value in enumerate(values):
                item = QTableWidgetItem(value)
                if c in {1, 2}:
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, c, item)

    def on_export_csv(self) -> None:
        out = "calendar_export.csv"
        export_csv(self.events, out)
        QMessageBox.information(self, "완료", f"CSV 내보내기 완료: {out}")

    def on_export_png(self) -> None:
        try:
            out = export_month_png(self.events, "calendar_month.png")
            QMessageBox.information(self, "완료", f"PNG 내보내기 완료: {out}")
        except Exception as exc:  # pragma: no cover - UI runtime feedback
            QMessageBox.warning(self, "실패", f"PNG 내보내기 실패: {exc}")
