from __future__ import annotations

from datetime import date
from pathlib import Path

from .models import Evidence, ReportData

REPORT_TEMPLATE_KEYS = [
    "one_line_conclusion",
    "nvidia_new_investments",
    "nvidia_exits_reductions",
    "nvidia_strategic_signal_facts",
    "nvidia_strategic_signal_interpretation",
    "ark_top_buys",
    "ark_top_sells",
    "ark_repeated_trends",
    "ark_strategic_signal_facts",
    "ark_strategic_signal_interpretation",
    "gpu_facts",
    "ai_cloud_facts",
    "data_center_facts",
    "storage_facts",
    "energy_facts",
    "bullish_signals",
    "bearish_signals",
    "watchlist",
    "risk_warning",
    "next_week_watch",
]


def render_markdown(data: ReportData, sections: dict[str, object]) -> str:
    lines = [
        "# AI Capital Flow Weekly",
        "",
        f"Report date: {data.report_date.isoformat()}",
        "",
        "## 1. One-line conclusion",
        str(sections["one_line_conclusion"]),
        "",
        "## 2. NVIDIA Portfolio",
        "- New investments:",
        *bullets(sections["nvidia_new_investments"], indent="  "),
        "- Exits / reductions:",
        *bullets(sections["nvidia_exits_reductions"], indent="  "),
        "- Strategic signal:",
        "  - Facts:",
        *bullets(sections["nvidia_strategic_signal_facts"], indent="    "),
        "  - Interpretation:",
        *bullets(sections["nvidia_strategic_signal_interpretation"], indent="    "),
        "",
        "## 3. Cathie Wood / ARK",
        "- Top buys:",
        *bullets(sections["ark_top_buys"], indent="  "),
        "- Top sells:",
        *bullets(sections["ark_top_sells"], indent="  "),
        "- Repeated trends:",
        *bullets(sections["ark_repeated_trends"], indent="  "),
        "- Strategic signal:",
        "  - Facts:",
        *bullets(sections["ark_strategic_signal_facts"], indent="    "),
        "  - Interpretation:",
        *bullets(sections["ark_strategic_signal_interpretation"], indent="    "),
        "",
        "## 4. AI Infrastructure Signals",
        "- GPU:",
        *bullets(sections["gpu_facts"], indent="  "),
        "- AI cloud:",
        *bullets(sections["ai_cloud_facts"], indent="  "),
        "- Data center:",
        *bullets(sections["data_center_facts"], indent="  "),
        "- Storage:",
        *bullets(sections["storage_facts"], indent="  "),
        "- Energy:",
        *bullets(sections["energy_facts"], indent="  "),
        "",
        "## 5. Investment Implications",
        "- Bullish signals:",
        *bullets(sections["bullish_signals"], indent="  "),
        "- Bearish signals:",
        *bullets(sections["bearish_signals"], indent="  "),
        "- Watchlist:",
        *bullets(sections["watchlist"], indent="  "),
        "- Risk warning:",
        *bullets([sections["risk_warning"]], indent="  "),
        "",
        "## 6. Next Week Watch",
        *bullets(sections["next_week_watch"]),
        "",
        "## Source Log",
        *source_log(data.evidence),
        "",
    ]
    return "\n".join(lines)


def write_report(markdown: str, output_dir: Path, report_date: date) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{report_date.isoformat()}.md"
    path.write_text(markdown, encoding="utf-8")
    return path


def bullets(value: object, indent: str = "") -> list[str]:
    if value is None:
        return [f"{indent}- No evidence collected."]
    if isinstance(value, str):
        values = [value]
    else:
        values = list(value) if isinstance(value, list) else [str(value)]
    if not values:
        return [f"{indent}- No evidence collected."]
    return [f"{indent}- {item}" for item in values]


def source_log(evidence: list[Evidence]) -> list[str]:
    if not evidence:
        return ["- No sources collected."]
    return [
        f"- [{item.tier}] {item.source}: [{item.title}]({item.url})"
        for item in evidence
        if item.url
    ]
