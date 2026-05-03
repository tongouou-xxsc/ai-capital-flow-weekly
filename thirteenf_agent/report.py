from __future__ import annotations

from datetime import date
from pathlib import Path

from .analysis import key_bottleneck, sector_flow, sector_totals
from .models import AnalysisResult, PositionChange


def render_report(result: AnalysisResult) -> str:
    from_sector, to_sector = sector_flow(result.changes)
    bottleneck = key_bottleneck(result.changes)
    added = [change for change in result.changes if change.kind == "Added"]
    increased = [change for change in result.changes if change.kind == "Increased"]
    reduced = [change for change in result.changes if change.kind == "Reduced"]
    closed = [change for change in result.changes if change.kind == "Closed"]
    current_sectors = sector_totals(result.current_holdings)

    lines = [
        "# 13F Analysis Report",
        "",
        f"Fund: {result.fund_name}",
        f"CIK: {result.cik}",
        f"Current filing: {result.current_filing.form} filed {result.current_filing.filing_date}, report date {result.current_filing.report_date}",
        f"Previous filing: {result.previous_filing.form} filed {result.previous_filing.filing_date}, report date {result.previous_filing.report_date}",
        "",
        "## One-line Conclusion",
        f"Funds moved from {from_sector} to {to_sector}.",
        "",
        "## Key Changes",
        "### Added",
        *change_lines(added[:10]),
        "",
        "### Increased",
        *change_lines(increased[:10]),
        "",
        "### Reduced",
        *change_lines(reduced[:10]),
        "",
        "### Closed",
        *change_lines(closed[:10]),
        "",
        "## Sector Shift",
        f"- From {from_sector} to {to_sector}",
        f"- Current sector exposure: {format_sector_totals(current_sectors)}",
        "",
        "## Core Thesis",
        f"This portfolio is betting on {to_sector}, with the key AI bottleneck appearing to be {bottleneck}.",
        "",
        "## Investment Implications",
        "- Bullish:",
        f"  - Rising exposure to {to_sector} may signal conviction in that part of the AI infrastructure stack.",
        "- Bearish:",
        f"  - Reductions or closures in {from_sector} may indicate valuation concern, profit-taking, or rotation away from prior winners.",
        "- Watchlist:",
        f"  - Monitor whether {bottleneck} exposure expands again next quarter.",
        "  - Confirm whether changes are broad sector rotation or single-name position sizing.",
        "",
        "## Next Validation Points",
        "- Check the next 13F filing for repeated additions in the same sector.",
        "- Compare position changes with earnings commentary, capex plans, and valuation.",
        "- Verify whether options, private holdings, or non-13F assets change the full picture.",
        "",
        "## Sources",
        f"- Current filing: {result.current_filing.url}",
        f"- Previous filing: {result.previous_filing.url}",
        "",
    ]
    return "\n".join(lines)


def change_lines(changes: list[PositionChange]) -> list[str]:
    if not changes:
        return ["- None detected."]
    return [
        (
            f"- {change.issuer} ({change.sector}): "
            f"{money(change.previous_value_usd)} -> {money(change.current_value_usd)}, "
            f"shares {change.previous_shares:,} -> {change.current_shares:,}"
        )
        for change in changes
    ]


def format_sector_totals(totals: dict[str, int]) -> str:
    if not totals:
        return "No holdings parsed."
    ordered = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    return ", ".join(f"{sector} {money(value)}" for sector, value in ordered)


def money(value: int) -> str:
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000_000:
        return f"{sign}${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{sign}${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{sign}${value / 1_000:.1f}K"
    return f"{sign}${value}"


def save_report(markdown: str, output_dir: Path, report_date: date) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{report_date.isoformat()}.md"
    path.write_text(markdown, encoding="utf-8")
    return path
