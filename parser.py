from __future__ import annotations

from datetime import date
from pathlib import Path

from models import Event


TABLE_HEADERS = {
    "title": {"title", "제목"},
    "start": {"start", "시작일", "start_date"},
    "end": {"end", "종료일", "end_date"},
    "status": {"status", "상태"},
    "tags": {"tags", "태그"},
    "platforms": {"platform", "platforms", "플랫폼"},
    "url": {"url", "링크"},
}


def parse_calendar_markdown(path: str | Path) -> list[Event]:
    """Parse calendar markdown and return Event objects.

    Supports two lightweight formats:
    1) Markdown table with header fields like 제목/시작일/종료일/상태/태그/플랫폼/URL.
    2) Bullet lines: `- 제목 | YYYY-MM-DD ~ YYYY-MM-DD | 상태 | 태그1,태그2 | PC,PS5 | URL`.
    """

    file_path = Path(path)
    if not file_path.exists():
        return []

    lines = file_path.read_text(encoding="utf-8").splitlines()
    table_events = _parse_table(lines)
    if table_events:
        return table_events
    return _parse_bullets(lines)


def _parse_table(lines: list[str]) -> list[Event]:
    header_map: dict[str, int] = {}
    events: list[Event] = []

    for idx, raw in enumerate(lines):
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not header_map:
            normalized = [c.lower().replace(" ", "") for c in cells]
            for key, aliases in TABLE_HEADERS.items():
                for i, item in enumerate(normalized):
                    if item in aliases:
                        header_map[key] = i
                        break
            continue

        if idx == 1 and all(set(c) <= {"-", ":"} for c in cells):
            continue
        if not cells or all(not c for c in cells):
            continue

        event = _event_from_cells(cells, header_map, raw)
        events.append(event)

    return events


def _event_from_cells(cells: list[str], header_map: dict[str, int], raw: str) -> Event:
    def cell(name: str) -> str:
        i = header_map.get(name)
        if i is None or i >= len(cells):
            return ""
        return cells[i].strip()

    start_date = _parse_date(cell("start"))
    end_date = _parse_date(cell("end"))
    if end_date is None:
        end_date = start_date

    return Event(
        title=cell("title"),
        start_date=start_date,
        end_date=end_date,
        status=cell("status") or "미정",
        tags=_split_list(cell("tags")),
        platforms=_split_list(cell("platforms")),
        url=cell("url"),
        raw_line=raw,
        is_valid=bool(cell("title") and start_date),
    )


def _parse_bullets(lines: list[str]) -> list[Event]:
    events: list[Event] = []
    for raw in lines:
        line = raw.strip()
        if not line.startswith("-"):
            continue
        parts = [p.strip() for p in line.lstrip("- ").split("|")]
        if len(parts) < 2:
            continue

        title = parts[0]
        date_token = parts[1]
        start_token, end_token = _split_date_range(date_token)
        start_date = _parse_date(start_token)
        end_date = _parse_date(end_token) if end_token else start_date

        status = parts[2] if len(parts) > 2 else "미정"
        tags = _split_list(parts[3]) if len(parts) > 3 else []
        platforms = _split_list(parts[4]) if len(parts) > 4 else []
        url = parts[5] if len(parts) > 5 else ""

        events.append(
            Event(
                title=title,
                start_date=start_date,
                end_date=end_date,
                status=status,
                tags=tags,
                platforms=platforms,
                url=url,
                raw_line=raw,
                is_valid=bool(title and start_date),
            )
        )
    return events


def _split_date_range(value: str) -> tuple[str, str]:
    if "~" in value:
        left, right = value.split("~", 1)
        return left.strip(), right.strip()
    return value.strip(), ""


def _split_list(value: str) -> list[str]:
    if not value:
        return []
    cleaned = value.replace("/", ",")
    return [item.strip() for item in cleaned.split(",") if item.strip()]


def _parse_date(value: str) -> date | None:
    value = value.strip()
    if not value:
        return None
    normalized = value.replace(".", "-").replace("/", "-")
    try:
        return date.fromisoformat(normalized)
    except ValueError:
        return None
