from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Filing:
    accession: str
    filing_date: str
    report_date: str
    form: str
    primary_document: str
    url: str


@dataclass(frozen=True)
class Holding:
    issuer: str
    cusip: str
    title: str
    value_usd: int
    shares: int
    sector: str

    @property
    def key(self) -> str:
        return self.cusip or self.issuer.upper()


@dataclass(frozen=True)
class PositionChange:
    kind: str
    issuer: str
    cusip: str
    sector: str
    current_value_usd: int
    previous_value_usd: int
    current_shares: int
    previous_shares: int

    @property
    def value_delta(self) -> int:
        return self.current_value_usd - self.previous_value_usd

    @property
    def share_delta(self) -> int:
        return self.current_shares - self.previous_shares


@dataclass
class AnalysisResult:
    fund_name: str
    cik: str
    report_date: date
    current_filing: Filing
    previous_filing: Filing
    changes: list[PositionChange] = field(default_factory=list)
    current_holdings: list[Holding] = field(default_factory=list)
    previous_holdings: list[Holding] = field(default_factory=list)
    source_urls: list[str] = field(default_factory=list)
