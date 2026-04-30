from __future__ import annotations

from datetime import date
from html import escape
from pathlib import Path
import re

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
    html_path = output_dir / f"{report_date.isoformat()}.html"
    html_path.write_text(render_html(markdown), encoding="utf-8")
    return path


def render_html(markdown: str) -> str:
    body: list[str] = []
    in_list = False
    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if not line:
            if in_list:
                body.append("</ul>")
                in_list = False
            continue
        if line.startswith("# "):
            if in_list:
                body.append("</ul>")
                in_list = False
            body.append(f"<h1>{inline_html(line[2:])}</h1>")
        elif line.startswith("## "):
            if in_list:
                body.append("</ul>")
                in_list = False
            body.append(f"<h2>{inline_html(line[3:])}</h2>")
        elif line.lstrip().startswith("- "):
            if not in_list:
                body.append("<ul>")
                in_list = True
            body.append(f"<li>{inline_html(line.lstrip()[2:])}</li>")
        else:
            if in_list:
                body.append("</ul>")
                in_list = False
            body.append(f"<p>{inline_html(line)}</p>")
    if in_list:
        body.append("</ul>")
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>AI Capital Flow Weekly</title>",
            "<style>",
            "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;line-height:1.55;max-width:920px;margin:32px auto;padding:0 18px;color:#1f2937;background:#fff}",
            "h1{font-size:32px;margin-bottom:8px}h2{font-size:22px;margin-top:30px;border-bottom:1px solid #e5e7eb;padding-bottom:8px}",
            "ul{padding-left:22px}li{margin:8px 0}a{color:#2563eb}p{margin:10px 0}",
            "</style>",
            "</head>",
            "<body>",
            *body,
            "</body>",
            "</html>",
        ]
    )


def inline_html(text: str) -> str:
    escaped = escape(text)
    return re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: f'<a href="{escape(match.group(2), quote=True)}">{escape(match.group(1))}</a>',
        escaped,
    )


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
