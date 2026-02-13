from __future__ import annotations

import csv
from pathlib import Path

from PySide6.QtWidgets import QWidget

from models import Event


def export_csv(events: list[Event], invalid_events: list[Event], output_path: str | Path) -> Path:
    out = Path(output_path)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "제목",
                "시작일",
                "종료일",
                "상태",
                "태그",
                "플랫폼",
                "장르",
                "설명",
                "URL",
                "유효",
                "오류",
                "원문",
            ]
        )
        for e in events + invalid_events:
            writer.writerow(
                [
                    e.title,
                    e.start_date.isoformat() if e.start_date else "",
                    e.end_date.isoformat() if e.end_date else "",
                    e.status.value,
                    ",".join(e.emoji_tags),
                    ",".join(e.platforms),
                    ",".join(e.genres),
                    e.description,
                    e.url,
                    "Y" if e.is_valid else "N",
                    e.error_message or "",
                    e.raw_line.strip(),
                ]
            )
    return out


def export_month_png(
    target_widget: QWidget, year: int, month: int, output_path: str | Path | None = None
) -> Path:
    out = Path(output_path) if output_path else Path(f"calendar_{year:04d}-{month:02d}.png")
    pixmap = target_widget.grab()
    pixmap.save(str(out), "PNG")
    return out
