from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class EventStatus(str, Enum):
    CONFIRMED = "확정"
    OFFICIAL = "공식"
    EXPECTED = "예상"
    UNSURE = "확실하지 않음"
    UNKNOWN = "미분류"


@dataclass(slots=True)
class Event:
    title: str
    start_date: date | None
    end_date: date | None
    status: EventStatus
    emoji_tags: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)
    genres: list[str] = field(default_factory=list)
    description: str = ""
    url: str = ""
    raw_line: str = ""
    is_valid: bool = True
    error_message: str | None = None
    approx_month: bool = False
    section_month: tuple[int, int] | None = None

    def date_range_str(self) -> str:
        if not self.start_date and not self.end_date:
            return ""
        if not self.end_date or self.start_date == self.end_date:
            return self.start_date.isoformat() if self.start_date else ""
        return f"{self.start_date.isoformat()} ~ {self.end_date.isoformat()}"

    def includes_date(self, day: date) -> bool:
        if not self.start_date:
            return False
        end = self.end_date or self.start_date
        return self.start_date <= day <= end

    def intersects_month(self, year: int, month: int) -> bool:
        if not self.start_date:
            return False

        from calendar import monthrange

        start = self.start_date
        end = self.end_date or self.start_date
        first = date(year, month, 1)
        last = date(year, month, monthrange(year, month)[1])
        return not (end < first or start > last)

    def matches_query(self, query: str) -> bool:
        token = query.strip().lower()
        if not token:
            return True

        haystack = " ".join(
            [
                self.title,
                self.description,
                " ".join(self.platforms),
                " ".join(self.genres),
                " ".join(self.emoji_tags),
                self.status.value,
            ]
        ).lower()
        return token in haystack
