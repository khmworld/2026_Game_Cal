from __future__ import annotations

import os
import sys
import traceback
from datetime import date
from pathlib import Path

from PySide6.QtCore import QLockFile, Qt
from PySide6.QtGui import QFont, QFontDatabase, QGuiApplication, QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from parser import parse_calendar_markdown
from ui_main import GameCalendarWindow

SAMPLE_MARKDOWN = """# 2026 게임/시즌/이벤트 캘린더
## 2월 2026
- 2026-02-20 🔁 Diablo II: Resurrected Ladder 시즌 13 시작 [확정] (https://example.com)
- 2026-02-23 ~ 2026-03-02 [확정] Steam Next Fest (Feb 2026)
- 2026-02 [예상] 대형 시즌 업데이트
"""

_APP_LOCK: QLockFile | None = None


def app_directory() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resource_path(name: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", app_directory()))
    return base / name


def ensure_calendar_file(path: str | Path) -> tuple[Path, bool]:
    target = Path(path)
    created = False
    if not target.exists():
        target.write_text(SAMPLE_MARKDOWN, encoding="utf-8")
        created = True
    return target, created


def pick_app_font() -> QFont:
    available = {name.lower() for name in QFontDatabase.families()}
    if "sf pro display" in available:
        return QFont("SF Pro Display", 10)
    if "segoe ui" in available:
        return QFont("Segoe UI", 10)
    if "inter" in available:
        return QFont("Inter", 10)
    return QFont("Malgun Gothic", 10)


def detect_dark_mode() -> bool:
    try:
        return QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except Exception:
        return False


def load_style(app: QApplication) -> None:
    qss = resource_path("ui_style.qss")
    if qss.exists():
        app.setStyleSheet(qss.read_text(encoding="utf-8"))


def _resolve_icon_path() -> Path | None:
    candidates = [
        resource_path("assets/app_icon.png"),
        resource_path("app_icon.png"),
        app_directory() / "assets" / "app_icon.png",
        app_directory() / "app_icon.png",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _initial_month(events) -> tuple[int, int]:
    valid_dates = [e.start_date for e in events if e.start_date]
    if not valid_dates:
        now = date.today()
        return now.year, now.month
    first = min(valid_dates)
    return first.year, first.month


def main() -> int:
    global _APP_LOCK

    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

    app: QApplication | None = None
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Game Calendar")
        icon_path = _resolve_icon_path()
        if icon_path is not None:
            app.setWindowIcon(QIcon(str(icon_path)))
        app.setFont(pick_app_font())
        load_style(app)

        _APP_LOCK = QLockFile(str(app_directory() / "gamecalendar.lock"))
        _APP_LOCK.setStaleLockTime(30_000)
        if not _APP_LOCK.tryLock(100):
            QMessageBox.warning(
                None,
                "이미 실행 중",
                "Game Calendar가 이미 실행 중입니다.\n기존 창을 종료한 뒤 다시 실행하세요.",
            )
            return 0

        cal_path, created = ensure_calendar_file(app_directory() / "calendar.md")
        events, invalid_events = parse_calendar_markdown(cal_path)
        initial_year, initial_month = _initial_month(events)

        window = GameCalendarWindow(
            events=events,
            invalid_events=invalid_events,
            source_path=str(cal_path),
            initial_year=initial_year,
            initial_month=initial_month,
            dark_mode=detect_dark_mode(),
        )
        if icon_path is not None:
            window.setWindowIcon(QIcon(str(icon_path)))
        window.show()

        if created:
            QMessageBox.information(
                window,
                "샘플 파일 생성",
                f"calendar.md가 없어 샘플 파일을 생성했습니다.\n경로: {cal_path}",
            )
        return app.exec()
    except Exception:
        log_path = app_directory() / "gamecalendar_error.log"
        log_path.write_text(traceback.format_exc(), encoding="utf-8")
        if app is not None:
            QMessageBox.critical(
                None,
                "실행 오류",
                f"앱 실행 중 오류가 발생했습니다.\n로그 파일: {log_path}",
            )
        return 1
    finally:
        if _APP_LOCK is not None and _APP_LOCK.isLocked():
            _APP_LOCK.unlock()


if __name__ == "__main__":
    raise SystemExit(main())
