from __future__ import annotations

import argparse
from datetime import date

from .analysis import compare_holdings
from .config import load_settings
from .models import AnalysisResult
from .report import render_report, save_report
from .sec_client import SecClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze a fund's latest two 13F filings.")
    parser.add_argument("--fund", required=True, help='Fund or manager name, e.g. "Situational Awareness LP".')
    parser.add_argument("--cik", help="Optional SEC CIK. Use this if fund-name matching is imperfect.")
    parser.add_argument("--date", help="Report date in YYYY-MM-DD format. Defaults to today.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings()
    report_date = date.fromisoformat(args.date) if args.date else date.today()
    sec = SecClient(settings.sec_user_agent)

    if args.cik:
        cik = args.cik.zfill(10)
        matched_name = args.fund
    else:
        cik, matched_name = sec.resolve_cik(args.fund)

    filings = sec.fetch_recent_13f_filings(cik, limit=2)
    current_holding = sec.fetch_holdings(cik, filings[0])
    previous_holding = sec.fetch_holdings(cik, filings[1])
    changes = compare_holdings(current_holding, previous_holding)

    result = AnalysisResult(
        fund_name=matched_name,
        cik=cik,
        report_date=report_date,
        current_filing=filings[0],
        previous_filing=filings[1],
        changes=changes,
        current_holdings=current_holding,
        previous_holdings=previous_holding,
        source_urls=[filings[0].url, filings[1].url],
    )
    markdown = render_report(result)
    path = save_report(markdown, settings.output_dir, report_date)
    print(f"Report written to {path}")


if __name__ == "__main__":
    main()
