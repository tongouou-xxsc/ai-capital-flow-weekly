from __future__ import annotations

from .config import Settings
from .models import Evidence, ReportData


def build_report_sections(data: ReportData, settings: Settings) -> dict[str, object]:
    nvidia_items = data.by_category("nvidia")
    nvidia = cite_list(nvidia_items[:8])
    nvidia_new = cite_list([item for item in nvidia_items if "new positions" in item.title.lower()])
    nvidia_exits = cite_list(
        [item for item in nvidia_items if "exited positions" in item.title.lower() or "reduced positions" in item.title.lower()]
    )
    nvidia_warning = cite_list([item for item in nvidia_items if "collection warning" in item.title.lower()])
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
        "nvidia_new_investments": nvidia_new or nvidia_warning or ["No new NVIDIA 13F positions or NVentures additions were confirmed in collected evidence."],
        "nvidia_exits_reductions": nvidia_exits or nvidia_warning or ["No NVIDIA 13F exits or reductions were confirmed in collected evidence."],
        "nvidia_strategic_signal_facts": nvidia_new + nvidia_exits + nvidia_warning + nvidia[:4],
        "nvidia_strategic_signal_interpretation": [
            "Interpretation: NVIDIA-linked capital flows should be weighted more heavily when confirmed by SEC filings or NVentures portfolio updates. If SEC collection fails, do not infer that NVIDIA made no changes."
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
        and "holdings warning" not in item.title.lower()
    ]
