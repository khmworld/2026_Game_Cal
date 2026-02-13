from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(slots=True)
class Event:
    """Parsed game schedule event."""

    title: str
    start_date: date | None
    end_date: date | None
    status: str
    tags: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)
    url: str = ""
    raw_line: str = ""
    is_valid: bool = True
