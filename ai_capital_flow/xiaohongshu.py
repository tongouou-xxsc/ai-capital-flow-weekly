from __future__ import annotations

import argparse
import re
from pathlib import Path


def build_xiaohongshu_post(report_markdown: str) -> str:
    report_date = extract_after(report_markdown, "Report date:") or "this week"
    conclusion = section_text(report_markdown, "## 1. One-line conclusion", "## 2.")
    nvidia = section_text(report_markdown, "## 2. NVIDIA Portfolio", "## 3.")
    ark = section_text(report_markdown, "## 3. Cathie Wood / ARK", "## 4.")
    infra = section_text(report_markdown, "## 4. AI Infrastructure Signals", "## 5.")
    implications = section_text(report_markdown, "## 5. Investment Implications", "## 6.")

    lines = [
        f"AI资金流周报｜{report_date}",
        "",
        "一句话结论：",
        compact(conclusion),
        "",
        "1. NVIDIA",
        top_bullets(nvidia, limit=3),
        "",
        "2. ARK / Cathie Wood",
        top_bullets(ark, limit=4),
        "",
        "3. AI基础设施信号",
        top_bullets(infra, limit=5),
        "",
        "4. 投资含义",
        top_bullets(implications, limit=4),
        "",
        "我的观察：",
        "AI交易正在从“谁有AI概念”转向“谁控制算力、云、数据中心、电力和真实资本流”。后续重点看：NVDA 13F变化、ARK连续买卖方向、云厂商AI capex、数据中心电力约束。",
        "",
        "风险提示：",
        "仅为公开信息整理和研究记录，不构成投资建议。原始来源和完整链接见同日期 Markdown 周报。",
        "",
        "#AI投资 #英伟达 #ARKInvest #CathieWood #人工智能 #美股 #数据中心 #算力 #投资研究",
        "",
    ]
    return "\n".join(lines)


def section_text(markdown: str, start_heading: str, next_heading_prefix: str) -> str:
    start = markdown.find(start_heading)
    if start == -1:
        return ""
    body_start = start + len(start_heading)
    next_match = re.search(rf"\n{re.escape(next_heading_prefix)}", markdown[body_start:])
    if not next_match:
        return markdown[body_start:].strip()
    return markdown[body_start : body_start + next_match.start()].strip()


def extract_after(markdown: str, marker: str) -> str:
    for line in markdown.splitlines():
        if line.startswith(marker):
            return line.removeprefix(marker).strip()
    return ""


def top_bullets(text: str, limit: int) -> str:
    candidates = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        value = stripped[2:].strip()
        if value.endswith(":") or value in {"Facts:", "Interpretation:"}:
            continue
        value = re.sub(r"\s*Source:\s*\S+", "", value).strip()
        if value and value not in candidates:
            candidates.append(value)
    return "\n".join(f"- {item}" for item in candidates[:limit]) or "- 本周没有足够的新信号。"


def compact(text: str) -> str:
    value = re.sub(r"\s+", " ", text).strip()
    return value or "本周没有足够的新结论。"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a Xiaohongshu-ready draft from a weekly report.")
    parser.add_argument("report", help="Path to reports/YYYY-MM-DD.md")
    parser.add_argument("--output-dir", default="social_posts", help="Directory for Xiaohongshu drafts.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report_path = Path(args.report)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    post = build_xiaohongshu_post(report_path.read_text(encoding="utf-8"))
    output_path = output_dir / f"{report_path.stem}-xiaohongshu.md"
    output_path.write_text(post, encoding="utf-8")
    print(f"Xiaohongshu draft written to {output_path}")


if __name__ == "__main__":
    main()
