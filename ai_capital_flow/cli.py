from __future__ import annotations

import argparse
from datetime import datetime, date
from zoneinfo import ZoneInfo

from .analyzer import build_report_sections
from .config import load_settings
from .models import ReportData
from .render import render_markdown, write_report
from .sources import SourceClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate AI Capital Flow Weekly report.")
    parser.add_argument("--date", help="Report date in YYYY-MM-DD format. Defaults to today in REPORT_TIMEZONE.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings()
    report_date = (
        date.fromisoformat(args.date)
        if args.date
        else datetime.now(ZoneInfo(settings.timezone)).date()
    )
    client = SourceClient(settings)
    evidence = client.collect(report_date)
    data = ReportData(report_date=report_date, lookback_days=settings.lookback_days, evidence=evidence)
    sections = build_report_sections(data, settings)
    markdown = render_markdown(data, sections)
    path = write_report(markdown, settings.output_dir, report_date)
    print(f"Report written to {path}")


if __name__ == "__main__":
    main()
