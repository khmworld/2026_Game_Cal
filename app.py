from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from parser import parse_calendar_markdown
from ui_main import GameCalendarWindow

SAMPLE_MARKDOWN = """# Game Calendar

| 제목 | 시작일 | 종료일 | 상태 | 태그 | 플랫폼 | URL |
| --- | --- | --- | --- | --- | --- | --- |
| 샘플 게임 런칭 | 2026-01-15 | 2026-01-15 | 출시 | RPG,신작 | PC,PS5 | https://example.com |
| 샘플 CBT | 2026-01-20 | 2026-01-25 | 테스트 | CBT | Mobile | https://example.com/cbt |
"""


def ensure_calendar_file(path: str | Path) -> Path:
    target = Path(path)
    if not target.exists():
        target.write_text(SAMPLE_MARKDOWN, encoding="utf-8")
    return target


def load_style(app: QApplication, qss_path: str | Path) -> None:
    path = Path(qss_path)
    if path.exists():
        app.setStyleSheet(path.read_text(encoding="utf-8"))


def main() -> int:
    os.environ.setdefault("PYTHONUTF8", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("Game Calendar")
    app.setFont(QFont("Malgun Gothic", 10))

    load_style(app, "ui_style.qss")

    calendar_path = ensure_calendar_file("calendar.md")
    events = parse_calendar_markdown(calendar_path)

    window = GameCalendarWindow(events, str(calendar_path))
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
