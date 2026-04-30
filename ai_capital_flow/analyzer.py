from __future__ import annotations

import json
from textwrap import dedent

from openai import OpenAI

from .config import Settings
from .models import Evidence, ReportData
from .render import REPORT_TEMPLATE_KEYS


def build_report_sections(data: ReportData, settings: Settings) -> dict[str, object]:
    if settings.openai_api_key:
        try:
            return build_with_openai(data, settings)
        except Exception as exc:
            fallback = build_fallback_sections(data)
            fallback["risk_warning"] = (
                f"OpenAI synthesis failed, so this report used deterministic summaries only. Error: {exc}"
            )
            return fallback
    return build_fallback_sections(data)


def build_with_openai(data: ReportData, settings: Settings) -> dict[str, object]:
    client = OpenAI(api_key=settings.openai_api_key)
    evidence_payload = [
        {
            "id": idx + 1,
            "title": item.title,
            "url": item.url,
            "source": item.source,
            "tier": item.tier,
            "category": item.category,
            "published_at": item.published_at,
            "summary": item.summary,
        }
        for idx, item in enumerate(data.evidence)
    ]
    prompt = dedent(
        f"""
        Create a concise one-page weekly AI investment report in structured JSON.
        Report date: {data.report_date.isoformat()}
        Lookback days: {data.lookback_days}

        Rules:
        - Separate facts from interpretation.
        - Every major claim must cite source URLs using evidence ids.
        - Prefer official evidence over secondary evidence.
        - Secondary evidence may confirm, not replace, official evidence.
        - If evidence is weak or missing, say so plainly.
        - Keep each bullet short.

        JSON keys required:
        {json.dumps(REPORT_TEMPLATE_KEYS)}

        Evidence:
        {json.dumps(evidence_payload, indent=2)}
        """
    )
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": "You are a careful investment research assistant. Return valid JSON only.",
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    content = response.choices[0].message.content or "{}"
    sections = json.loads(content)
    return {key: sections.get(key, default_for_key(key)) for key in REPORT_TEMPLATE_KEYS}


def build_fallback_sections(data: ReportData) -> dict[str, object]:
    nvidia_items = data.by_category("nvidia")
    nvidia = cite_list(nvidia_items[:8])
    nvidia_new = cite_list([item for item in nvidia_items if "new positions" in item.title.lower()])
    nvidia_exits = cite_list(
        [item for item in nvidia_items if "exited positions" in item.title.lower() or "reduced positions" in item.title.lower()]
    )
    ark_items = data.by_category("ark")
    ark = cite_list(ark_items[:12])
    ark_buys = cite_list([item for item in ark_items if "top buys" in item.title.lower()])
    ark_sells = cite_list([item for item in ark_items if "top sells" in item.title.lower()])
    ark_repeated = cite_list([item for item in ark_items if "repeated trade trends" in item.title.lower()])
    ark_holdings = cite_list([item for item in ark_items if "top holdings" in item.title.lower()])
    gpu = cite_list(data.by_category("infra_gpu")[:4])
    ai_cloud = cite_list(data.by_category("infra_ai_cloud")[:4])
    data_center = cite_list(data.by_category("infra_data_center")[:4])
    storage = cite_list(data.by_category("infra_storage")[:4])
    energy = cite_list(data.by_category("infra_energy")[:4])
    return {
        "one_line_conclusion": "Funds are moving from broad AI narratives to infrastructure bottlenecks and verified portfolio flows.",
        "nvidia_new_investments": nvidia_new or ["No new NVIDIA 13F positions or NVentures additions were confirmed in collected evidence."],
        "nvidia_exits_reductions": nvidia_exits or ["No NVIDIA 13F exits or reductions were confirmed in collected evidence."],
        "nvidia_strategic_signal_facts": nvidia,
        "nvidia_strategic_signal_interpretation": [
            "Interpretation: NVIDIA-linked capital flows should be weighted more heavily when confirmed by SEC filings or NVentures portfolio updates."
        ],
        "ark_top_buys": ark_buys or ["No public ARK buy table was collected; ARK's official trade page requires email subscription for daily trade detail."],
        "ark_top_sells": ark_sells or ["No public ARK sell table was collected; ARK's official trade page requires email subscription for daily trade detail."],
        "ark_repeated_trends": ark_repeated or ark_holdings,
        "ark_strategic_signal_facts": ark_buys + ark_sells + ark_repeated + ark_holdings[:4] or ark,
        "ark_strategic_signal_interpretation": [
            "Interpretation: repeated ARK activity can flag high-conviction AI themes, but ETF flows and liquidity should be checked separately."
        ],
        "gpu_facts": gpu,
        "ai_cloud_facts": ai_cloud,
        "data_center_facts": data_center,
        "storage_facts": storage,
        "energy_facts": energy,
        "bullish_signals": [
            "Bullish: official evidence of rising capex, new GPU/cloud capacity, or strategic investments supports continued AI infrastructure demand."
        ],
        "bearish_signals": [
            "Bearish: supply constraints, power bottlenecks, stretched valuations, or portfolio reductions can weaken near-term risk/reward."
        ],
        "watchlist": ["NVDA 13F deltas", "ARK repeated buys/sells", "AI capex commentary", "Power and data-center constraints"],
        "risk_warning": "This report is research automation, not financial advice. Verify filings, timestamps, liquidity, and valuation before investing.",
        "next_week_watch": [
            "Latest NVIDIA SEC/NVentures updates.",
            "ARK daily trades and fund holdings changes.",
            "Hyperscaler AI capex, GPU availability, and data-center power commentary.",
        ],
    }


def cite_list(items: list[Evidence]) -> list[str]:
    return [
        f"{item.summary} Source: {item.url}"
        for item in items
        if item.summary
        and item.url
        and "no matching source-tier results" not in item.title.lower()
        and "search warning" not in item.title.lower()
    ]


def default_for_key(key: str) -> object:
    if key == "one_line_conclusion":
        return "Funds are moving from unverified AI exposure to source-confirmed AI infrastructure flows."
    if key == "risk_warning":
        return "This report is research automation, not financial advice."
    return []
