from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from models import Event, EventStatus

HEADER_PATTERNS = (
    re.compile(r"^\s*##\s*(\d{4})-(\d{1,2})\s*$"),
    re.compile(r"^\s*##\s*(\d{4})년\s*(\d{1,2})월\s*$"),
    re.compile(r"^\s*##\s*(\d{1,2})월\s*\([A-Za-z]+\s+(\d{4})\)\s*$"),
    re.compile(r"^\s*##\s*(\d{1,2})월\s*(?:\([A-Za-z]+\)\s*)?(\d{4})\s*$"),
    re.compile(r"^\s*##\s*([A-Za-z]+)\s+(\d{4})\s*$"),
)

MONTH_NAME_TO_NUM = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

LINE_PATTERN = re.compile(
    r"^(?P<date>\d{4}-\d{2}(?:-\d{2})?(?:\s*~\s*\d{4}-\d{2}(?:-\d{2})?)?)\s+(?P<rest>.+)$"
)
STATUS_PATTERN = re.compile(r"\*{0,2}\[(확정|공식|예상|확실하지 않음)\]\*{0,2}")
URL_PARENS_PATTERN = re.compile(r"\((https?://[^)]+)\)\s*$")
URL_INLINE_PATTERN = re.compile(r"(https?://\S+)")
CONTENT_REF_PATTERN = re.compile(r"\s*:contentReference\[.*$")

KNOWN_EMOJIS = (
    "🔁",
    "🎮",
    "⚔️",
    "🧠",
    "🌙",
    "📖",
    "🏁",
    "🧩",
    "🔥",
    "🛍️",
    "🧟",
    "✈️",
    "🔫",
    "🤖",
    "🌀",
    "🥊",
    "🚗",
    "🎉",
)

PLATFORM_PATTERN = re.compile(
    r"(?<![A-Z0-9])(PC|PS5|PS4|XSX\|S|XSX/S|XSX|XBOX|XBO|NS2|NS|WIN)(?![A-Z0-9])",
    re.IGNORECASE,
)
PLATFORM_NORMALIZE = {
    "XBOX": "XBO",
    "XSX/S": "XSX|S",
}

GENRE_KEYWORDS = (
    "액션 RPG",
    "RPG",
    "액션",
    "호러",
    "어드벤처",
    "FPS",
    "슈터",
    "대전",
    "레이싱",
    "전략",
    "카드",
    "확장팩",
    "세일",
    "페스트",
    "축제",
    "이벤트",
    "업데이트",
)


def parse_calendar_markdown(path: str | Path) -> tuple[list[Event], list[Event]]:
    file_path = Path(path)
    if not file_path.exists():
        return [], []

    lines = file_path.read_text(encoding="utf-8").splitlines()
    events: list[Event] = []
    invalid_events: list[Event] = []
    current_section: tuple[int, int] | None = None

    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue

        section = _parse_section_header(stripped)
        if section:
            current_section = section
            continue

        if not (stripped.startswith("-") or stripped.startswith("*")):
            continue
        if re.fullmatch(r"[-*]{3,}", stripped):
            continue

        candidate = stripped[1:].strip()
        if not re.match(r"^\d{4}-\d{2}", candidate):
            continue

        event = _parse_event_line(stripped, raw, current_section)
        if event.is_valid:
            events.append(event)
        else:
            invalid_events.append(event)

    return events, invalid_events


def _parse_section_header(line: str) -> tuple[int, int] | None:
    for i, pattern in enumerate(HEADER_PATTERNS):
        m = pattern.match(line)
        if not m:
            continue

        if i in (0, 1):
            year, month = int(m.group(1)), int(m.group(2))
        elif i in (2, 3):
            month, year = int(m.group(1)), int(m.group(2))
        else:
            month_name = m.group(1).lower()
            year = int(m.group(2))
            month = MONTH_NAME_TO_NUM.get(month_name, 0)

        if 1 <= month <= 12:
            return year, month

    return None


def _parse_event_line(line: str, raw_line: str, section: tuple[int, int] | None) -> Event:
    core = CONTENT_REF_PATTERN.sub("", line).strip().lstrip("-* ").strip()

    m = LINE_PATTERN.match(core)
    if not m:
        return _invalid_event(raw_line, "날짜 형식으로 시작하지 않습니다.", section)

    date_token = m.group("date").strip()
    rest = m.group("rest").strip()
    start_date, end_date, approx_month, date_error = _parse_date_token(date_token)

    status = EventStatus.UNKNOWN
    status_match = STATUS_PATTERN.search(rest)
    if status_match:
        status = _status_from_text(status_match.group(1))
        rest = (rest[: status_match.start()] + rest[status_match.end() :]).strip()

    text_without_url, url = _extract_url(rest)
    title_part, description = _split_title_and_description(text_without_url)

    emojis = _extract_emoji_tags(f"{title_part} {description}")
    platforms = _unique_preserve_order(
        _extract_parenthesized_platforms(title_part) + _extract_platforms(f"{title_part} {description}")
    )
    title = _remove_parenthesized_platforms(title_part).strip(" -")
    genres = _extract_genres(description)

    if not url and "steam" in f"{title} {description}".lower():
        url = "https://store.steampowered.com/sale/"

    is_valid = bool(title and start_date and not date_error)

    return Event(
        title=title or "(제목 없음)",
        start_date=start_date,
        end_date=end_date,
        status=status,
        emoji_tags=emojis,
        platforms=platforms,
        genres=genres,
        description=description,
        url=url,
        raw_line=raw_line,
        is_valid=is_valid,
        error_message=date_error,
        approx_month=approx_month,
        section_month=section,
    )


def _invalid_event(raw_line: str, message: str, section: tuple[int, int] | None) -> Event:
    return Event(
        title=raw_line.strip(),
        start_date=None,
        end_date=None,
        status=EventStatus.UNKNOWN,
        raw_line=raw_line,
        is_valid=False,
        error_message=message,
        section_month=section,
    )


def _parse_date_token(token: str) -> tuple[date | None, date | None, bool, str | None]:
    if "~" in token:
        left, right = [t.strip() for t in token.split("~", 1)]
    else:
        left, right = token.strip(), ""

    start, approx_start, err_start = _parse_single_date_or_month(left)
    if right:
        end, approx_end, err_end = _parse_single_date_or_month(right)
    else:
        end, approx_end, err_end = start, approx_start, None

    approx = bool(approx_start or approx_end)
    if start and end and end < start:
        return start, end, approx, "종료일이 시작일보다 빠릅니다."

    return start, end, approx, err_start or err_end


def _parse_single_date_or_month(token: str) -> tuple[date | None, bool, str | None]:
    normalized = token.strip().replace(".", "-").replace("/", "-")

    m_full = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", normalized)
    if m_full:
        y, m, d = map(int, m_full.groups())
        try:
            return date(y, m, d), False, None
        except ValueError:
            return None, False, "잘못된 날짜 형식입니다."

    m_month = re.fullmatch(r"(\d{4})-(\d{2})", normalized)
    if m_month:
        y, m = map(int, m_month.groups())
        try:
            return date(y, m, 1), True, None
        except ValueError:
            return None, True, "잘못된 월 형식입니다."

    return None, False, "지원하지 않는 날짜 형식입니다."


def _status_from_text(text: str) -> EventStatus:
    if text == "확정":
        return EventStatus.CONFIRMED
    if text == "공식":
        return EventStatus.OFFICIAL
    if text == "예상":
        return EventStatus.EXPECTED
    if text == "확실하지 않음":
        return EventStatus.UNSURE
    return EventStatus.UNKNOWN


def _extract_url(text: str) -> tuple[str, str]:
    m = URL_PARENS_PATTERN.search(text)
    if m:
        return text[: m.start()].strip(), m.group(1).strip()

    m = URL_INLINE_PATTERN.search(text)
    if m:
        return text[: m.start()].strip(), m.group(1).strip().rstrip(")")

    return text.strip(), ""


def _split_title_and_description(text: str) -> tuple[str, str]:
    for sep in (" — ", " - ", " – "):
        if sep in text:
            left, right = text.split(sep, 1)
            return left.strip(), right.strip()
    return text.strip(), ""


def _extract_parenthesized_platforms(text: str) -> list[str]:
    out: list[str] = []
    for chunk in re.findall(r"\(([^)]+)\)", text):
        out.extend(_extract_platforms(chunk))
    return _unique_preserve_order(out)


def _remove_parenthesized_platforms(text: str) -> str:
    return re.sub(r"\(([^)]+)\)", "", text).strip()


def _extract_platforms(text: str) -> list[str]:
    found: list[str] = []
    for m in PLATFORM_PATTERN.finditer(text.upper().replace("/", " ")):
        token = PLATFORM_NORMALIZE.get(m.group(1), m.group(1))
        found.append(token)
    return _unique_preserve_order(found)


def _extract_emoji_tags(text: str) -> list[str]:
    return [emoji for emoji in KNOWN_EMOJIS if emoji in text]


def _extract_genres(description: str) -> list[str]:
    if not description:
        return []

    normalized = re.sub(r"\([^)]*\)", "", description).strip()
    genres: list[str] = []

    # 장르/이벤트 성격에 해당하는 키워드만 우선 추출해 필터 칩 난립을 방지한다.
    for keyword in GENRE_KEYWORDS:
        if keyword in normalized:
            genres.append(keyword)

    # 키워드가 없고 설명이 짧을 때만 원문을 장르로 사용한다.
    if not genres and 1 <= len(normalized) <= 18:
        genres.append(normalized)

    return _unique_preserve_order(genres)


def _unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []

    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)

    return out
