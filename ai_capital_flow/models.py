from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

SourceTier = Literal["official", "secondary"]


@dataclass(frozen=True)
class Evidence:
    title: str
    url: str
    source: str
    tier: SourceTier
    summary: str
    published_at: str | None = None
    category: str | None = None


@dataclass
class ReportData:
    report_date: date
    lookback_days: int
    evidence: list[Evidence] = field(default_factory=list)

    def by_category(self, category: str) -> list[Evidence]:
        return [item for item in self.evidence if item.category == category]
