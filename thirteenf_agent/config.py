from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    sec_user_agent: str
    output_dir: Path


def load_settings() -> Settings:
    load_dotenv()
    sec_user_agent = (os.getenv("SEC_USER_AGENT") or "13F Analysis Agent contact@example.com").strip()
    return Settings(
        sec_user_agent=sec_user_agent,
        output_dir=Path(os.getenv("REPORT_OUTPUT_DIR", "reports")),
    )
