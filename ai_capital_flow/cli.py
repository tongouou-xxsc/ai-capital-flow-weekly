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
    parser.add_argument(
        "--allow-sparse",
        action="store_true",
        help="Write a report even if key NVIDIA/ARK evidence is missing.",
    )
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
    if not args.allow_sparse:
        validate_evidence(evidence)
    data = ReportData(report_date=report_date, lookback_days=settings.lookback_days, evidence=evidence)
    sections = build_report_sections(data, settings)
    markdown = render_markdown(data, sections)
    path = write_report(markdown, settings.output_dir, report_date)
    print(f"Report written to {path}")


def validate_evidence(evidence: list) -> None:
    titles = [item.title.lower() for item in evidence]
    missing = []
    if not any("ark secondary top buys" in title for title in titles):
        missing.append("ARK top buys")
    if not any("ark secondary top sells" in title for title in titles):
        missing.append("ARK top sells")
    if not any("ark official" in title and "top holdings" in title for title in titles):
        missing.append("ARK official holdings")
    has_nvidia_comparison = any("nvidia 13f new positions" in title or "nvidia 13f exited positions" in title for title in titles)
    has_nvidia_warning = any("nvidia 13f collection warning" in title for title in titles)
    if not has_nvidia_comparison and not has_nvidia_warning:
        missing.append("NVIDIA 13F source status")
    if missing:
        collected_titles = "; ".join(item.title for item in evidence[:20]) or "none"
        raise RuntimeError(
            "Sparse report blocked. Missing: "
            + ", ".join(missing)
            + ". Check GitHub Secrets, especially SEC_USER_AGENT, and rerun. "
            + "Use --allow-sparse only if you intentionally want a source-page-only report. "
            + "Collected evidence titles: "
            + collected_titles
        )


if __name__ == "__main__":
    main()
