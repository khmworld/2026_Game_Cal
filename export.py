from __future__ import annotations

import calendar
import csv
from collections import defaultdict
from datetime import date
from pathlib import Path

from models import Event


def export_csv(events: list[Event], output_path: str | Path) -> Path:
    out = Path(output_path)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["제목", "시작일", "종료일", "상태", "태그", "플랫폼", "URL", "유효성"])
        for e in events:
            writer.writerow(
                [
                    e.title,
                    e.start_date.isoformat() if e.start_date else "",
                    e.end_date.isoformat() if e.end_date else "",
                    e.status,
                    ",".join(e.tags),
                    ",".join(e.platforms),
                    e.url,
                    "Y" if e.is_valid else "N",
                ]
            )
    return out


def export_month_png(events: list[Event], output_path: str | Path, month: date | None = None) -> Path:
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("matplotlib이 설치되어 있어야 PNG 내보내기를 사용할 수 있습니다.") from exc

    valid_dates = [e.start_date for e in events if e.start_date is not None]
    base = month or (min(valid_dates) if valid_dates else date.today())
    year, mon = base.year, base.month

    day_map: dict[int, list[str]] = defaultdict(list)
    for event in events:
        if not event.start_date or event.start_date.year != year or event.start_date.month != mon:
            continue
        day_map[event.start_date.day].append(event.title)

    cal = calendar.monthcalendar(year, mon)
    fig, ax = plt.subplots(figsize=(12, 8), dpi=150)
    ax.axis("off")

    headers = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cell_text = [headers]
    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append("")
            else:
                titles = "\n".join(day_map.get(day, [])[:2])
                row.append(f"{day}\n{titles}" if titles else str(day))
        cell_text.append(row)

    table = ax.table(cellText=cell_text, cellLoc="left", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 2.2)
    ax.set_title(f"Game Calendar - {year}-{mon:02d}", fontsize=14)

    out = Path(output_path)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    return out
