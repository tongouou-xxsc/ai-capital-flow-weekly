from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    sec_user_agent: str
    timezone: str
    lookback_days: int
    output_dir: Path
    ark_funds: tuple[str, ...]
    brave_search_api_key: str | None
    serpapi_api_key: str | None


def load_settings() -> Settings:
    load_dotenv()
    ark_funds = tuple(
        fund.strip().upper()
        for fund in os.getenv("ARK_FUNDS", "ARKK,ARKQ,ARKW,ARKG,ARKF,ARKX").split(",")
        if fund.strip()
    )
    return Settings(
        sec_user_agent=os.getenv("SEC_USER_AGENT") or "AI Capital Flow Weekly contact@example.com",
        timezone=os.getenv("REPORT_TIMEZONE", "America/New_York"),
        lookback_days=int(os.getenv("REPORT_LOOKBACK_DAYS", "7")),
        output_dir=Path(os.getenv("REPORT_OUTPUT_DIR", "reports")),
        ark_funds=ark_funds,
        brave_search_api_key=os.getenv("BRAVE_SEARCH_API_KEY") or None,
        serpapi_api_key=os.getenv("SERPAPI_API_KEY") or None,
    )
