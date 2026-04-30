from __future__ import annotations

import json
import re
from datetime import date, datetime
from typing import Iterable
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

from .config import Settings
from .models import Evidence

NVIDIA_CIK = "0001045810"

OFFICIAL_URLS = {
    "nvidia_ir": "https://investor.nvidia.com/financial-info/sec-filings/default.aspx",
    "nventures": "https://www.nventures.ai/portfolio/",
    "ark_trades": "https://ark-funds.com/trade-notifications/",
    "ark_funds": "https://ark-funds.com/funds/",
}

ARK_FUND_IDS = {
    "ARKQ": "1001",
    "ARKW": "1002",
    "ARKG": "1003",
    "ARKK": "1004",
    "ARKF": "1007",
    "ARKX": "1008",
}

SECONDARY_DOMAINS = [
    "fintel.io",
    "13f.info",
    "cathiesark.com",
    "reuters.com",
    "barrons.com",
    "finance.yahoo.com",
]

OFFICIAL_DOMAINS = [
    "investor.nvidia.com",
    "nvidia.com",
    "nventures.ai",
    "sec.gov",
    "ark-funds.com",
    "ir.amd.com",
    "amd.com",
    "abc.xyz",
    "microsoft.com",
    "ir.aboutamazon.com",
    "amazon.com",
    "investor.oracle.com",
    "oracle.com",
    "investor.meta.com",
    "meta.com",
    "investor.seagate.com",
    "investor.wdc.com",
    "investors.digitalrealty.com",
    "investor.equinix.com",
    "eia.gov",
    "energy.gov",
]

INFRA_QUERIES = {
    "gpu": "latest AI GPU demand supply NVIDIA AMD hyperscaler source official investor relations",
    "ai_cloud": "latest AI cloud capex GPU cloud source official investor relations",
    "data_center": "latest AI data center capex leasing power constraints source official",
    "storage": "latest AI storage demand data center SSD HDD source official investor relations",
    "energy": "latest data center power demand AI energy grid source official",
}

INFRA_OFFICIAL_EVIDENCE = {
    "gpu": [
        (
            "NVIDIA quarterly results",
            "https://investor.nvidia.com/financial-info/quarterly-results/default.aspx",
            "NVIDIA Investor Relations quarterly results are the primary official source for GPU/data-center revenue and demand commentary.",
        ),
        (
            "AMD investor relations",
            "https://ir.amd.com/financial-information/quarterly-results",
            "AMD quarterly results are an official source for accelerator and data-center commentary.",
        ),
    ],
    "ai_cloud": [
        (
            "Microsoft investor relations",
            "https://www.microsoft.com/en-us/Investor/earnings",
            "Microsoft earnings are an official source for Azure AI demand and cloud capex commentary.",
        ),
        (
            "Amazon investor relations",
            "https://ir.aboutamazon.com/quarterly-results/default.aspx",
            "Amazon quarterly results are an official source for AWS AI cloud demand and infrastructure investment commentary.",
        ),
        (
            "Alphabet investor relations",
            "https://abc.xyz/investor/",
            "Alphabet investor relations are an official source for Google Cloud AI demand and capex commentary.",
        ),
    ],
    "data_center": [
        (
            "Equinix investor relations",
            "https://investor.equinix.com/",
            "Equinix investor relations are an official source for data-center demand and leasing conditions.",
        ),
        (
            "Digital Realty investor relations",
            "https://investors.digitalrealty.com/",
            "Digital Realty investor relations are an official source for data-center demand and capacity signals.",
        ),
    ],
    "storage": [
        (
            "Seagate investor relations",
            "https://investors.seagate.com/",
            "Seagate investor relations are an official source for mass-capacity storage demand signals tied to cloud and AI data growth.",
        ),
        (
            "Western Digital investor relations",
            "https://investor.wdc.com/",
            "Western Digital investor relations are an official source for HDD, flash, and data-center storage demand commentary.",
        ),
    ],
    "energy": [
        (
            "U.S. EIA electricity data",
            "https://www.eia.gov/electricity/",
            "The U.S. Energy Information Administration is an official source for electricity market data relevant to data-center power demand.",
        ),
        (
            "U.S. DOE data centers and energy",
            "https://www.energy.gov/",
            "The U.S. Department of Energy is an official source for power, grid, and efficiency context around data-center growth.",
        ),
    ],
}


class SourceClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    def sec_headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.settings.sec_user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.sec.gov",
        }

    def sec_archive_headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.settings.sec_user_agent,
            "Accept-Encoding": "gzip, deflate",
        }

    def collect(self, report_date: date) -> list[Evidence]:
        evidence: list[Evidence] = []
        evidence.extend(self.collect_nvidia_13f(report_date))
        evidence.extend(self.collect_nventures())
        evidence.extend(self.collect_ark(report_date))
        evidence.extend(self.collect_infra_signals(report_date))
        return dedupe_evidence(evidence)

    def collect_nvidia_13f(self, report_date: date) -> list[Evidence]:
        evidence = [
            Evidence(
                title="NVIDIA SEC filings page",
                url=OFFICIAL_URLS["nvidia_ir"],
                source="NVIDIA Investor Relations",
                tier="official",
                category="nvidia",
                summary="Official NVIDIA Investor Relations page for SEC filings.",
            )
        ]
        try:
            submissions_url = f"https://data.sec.gov/submissions/CIK{NVIDIA_CIK}.json"
            response = self.session.get(submissions_url, headers=self.sec_headers(), timeout=30)
            response.raise_for_status()
            data = response.json()
            recent = data.get("filings", {}).get("recent", {})
            rows = zip(
                recent.get("accessionNumber", []),
                recent.get("form", []),
                recent.get("filingDate", []),
                recent.get("primaryDocument", []),
            )
            filings = [row for row in rows if row[1].startswith("13F-HR")]
            for accession, form, filing_date, primary_doc in filings[:2]:
                accession_no_dash = accession.replace("-", "")
                filing_url = (
                    f"https://www.sec.gov/Archives/edgar/data/{int(NVIDIA_CIK)}/"
                    f"{accession_no_dash}/{primary_doc}"
                )
                evidence.append(
                    Evidence(
                        title=f"NVIDIA {form} filed {filing_date}",
                        url=filing_url,
                        source="SEC EDGAR",
                        tier="official",
                        category="nvidia",
                        published_at=filing_date,
                        summary="Official 13F filing for NVIDIA institutional investment holdings.",
                    )
                )
            if len(filings) >= 2:
                latest = self.fetch_13f_holdings(filings[0][0])
                previous = self.fetch_13f_holdings(filings[1][0])
                if latest and previous:
                    evidence.extend(compare_13f_holdings(latest, previous, filings[0][2], filings[1][2]))
        except Exception as exc:
            evidence.append(
                Evidence(
                    title="NVIDIA 13F collection warning",
                    url=OFFICIAL_URLS["nvidia_ir"],
                    source="Collector",
                    tier="official",
                    category="nvidia",
                    summary=f"Could not fetch SEC submissions during this run: {exc}",
                )
            )
        evidence.extend(self.search_secondary("NVIDIA latest 13F changes new positions exits reductions", "nvidia", limit=3))
        return evidence

    def fetch_13f_holdings(self, accession: str) -> dict[str, int]:
        accession_no_dash = accession.replace("-", "")
        base_url = f"https://www.sec.gov/Archives/edgar/data/{int(NVIDIA_CIK)}/{accession_no_dash}/"
        index_response = self.session.get(urljoin(base_url, "index.json"), headers=self.sec_archive_headers(), timeout=30)
        index_response.raise_for_status()
        index = index_response.json()
        files = index.get("directory", {}).get("item", [])
        info_file = next(
            (
                item["name"]
                for item in files
                if item.get("name", "").lower().endswith(".xml")
                and "primary" not in item.get("name", "").lower()
                and "xsl" not in item.get("name", "").lower()
            ),
            None,
        )
        if not info_file:
            return {}
        xml_response = self.session.get(urljoin(base_url, info_file), headers=self.sec_archive_headers(), timeout=30)
        xml_response.raise_for_status()
        xml_text = xml_response.text
        root = ET.fromstring(xml_text.encode("utf-8"))
        holdings: dict[str, int] = {}
        for info in root.iter():
            if strip_ns(info.tag) != "infoTable":
                continue
            name = child_text(info, "nameOfIssuer")
            shares_text = child_text(info, "sshPrnamt")
            if not name or not shares_text:
                continue
            try:
                holdings[clean_text(name).upper()] = int(float(shares_text.replace(",", "")))
            except ValueError:
                continue
        return holdings

    def collect_nventures(self) -> list[Evidence]:
        evidence = [
            Evidence(
                title="NVentures portfolio",
                url=OFFICIAL_URLS["nventures"],
                source="NVentures",
                tier="official",
                category="nvidia",
                summary="Official NVentures portfolio page.",
            )
        ]
        try:
            html = self.session.get(OFFICIAL_URLS["nventures"], timeout=30).text
            soup = BeautifulSoup(html, "html.parser")
            names = []
            for text in soup.stripped_strings:
                if 2 <= len(text) <= 80 and not re.search(r"cookie|privacy|terms", text, re.I):
                    names.append(text)
            unique = list(dict.fromkeys(names))[:25]
            if unique:
                evidence.append(
                    Evidence(
                        title="NVentures visible portfolio names",
                        url=OFFICIAL_URLS["nventures"],
                        source="NVentures",
                        tier="official",
                        category="nvidia",
                        summary="Visible page text includes: " + ", ".join(unique[:15]),
                    )
                )
        except Exception as exc:
            evidence.append(
                Evidence(
                    title="NVentures collection warning",
                    url=OFFICIAL_URLS["nventures"],
                    source="Collector",
                    tier="official",
                    category="nvidia",
                    summary=f"Could not scrape NVentures portfolio during this run: {exc}",
                )
            )
        return evidence

    def collect_ark(self, report_date: date) -> list[Evidence]:
        evidence = [
            Evidence(
                title="ARK trade notifications",
                url=OFFICIAL_URLS["ark_trades"],
                source="ARK Invest",
                tier="official",
                category="ark",
                summary=(
                    "Official ARK Invest trade-notification page says ARK sends daily trade information for actively managed ETFs by email, "
                    "excluding IPO/secondary offering activity and ETF creation/redemption activity."
                ),
            ),
            Evidence(
                title="ARK ETF fund pages",
                url=OFFICIAL_URLS["ark_funds"],
                source="ARK Invest",
                tier="official",
                category="ark",
                summary="Official ARK Invest ETF fund pages and holdings entry point.",
            ),
        ]
        evidence.extend(self.collect_ark_holdings())
        evidence.extend(self.collect_cathiesark_trades())
        evidence.extend(self.search_secondary("Cathie Wood ARK daily trades top buys top sells latest", "ark", limit=4))
        return evidence

    def collect_ark_holdings(self) -> list[Evidence]:
        evidence: list[Evidence] = []
        for fund in self.settings.ark_funds:
            fund_url = f"https://ark-funds.com/funds/{fund.lower()}/"
            try:
                fund_id = self.discover_ark_fund_id(fund)
                if not fund_id:
                    evidence.append(
                        Evidence(
                            title=f"{fund} official fund page",
                            url=fund_url,
                            source="ARK Invest",
                            tier="official",
                            category="ark",
                            summary=f"Official {fund} fund page; holdings link was not visible in static HTML.",
                        )
                    )
                    continue
                holding = self.fetch_ark_holdings(fund, fund_id)
                if holding:
                    evidence.append(holding)
            except Exception as exc:
                evidence.append(
                    Evidence(
                        title=f"{fund} holdings warning",
                        url=fund_url,
                        source="Collector",
                        tier="official",
                        category="ark",
                        summary=f"Could not inspect {fund} fund page during this run: {exc}",
                    )
                )
        return evidence

    def discover_ark_fund_id(self, fund: str) -> str | None:
        if fund in ARK_FUND_IDS:
            return ARK_FUND_IDS[fund]
        fund_url = f"https://ark-funds.com/funds/{fund.lower()}/"
        html = self.session.get(fund_url, timeout=20).text
        match = re.search(r"/api/fund/holdings/(\d+)", html)
        return match.group(1) if match else None

    def fetch_ark_holdings(self, fund: str, fund_id: str) -> Evidence | None:
        data = {
            "Heading": "Top 10 Holdings",
            "PdfLinkText": "Full Holdings PDF",
            "CsvLinkText": "Full Holdings CSV",
            "Link": {"Style": "", "Href": "", "Aria": "", "Target": "", "Text": ""},
        }
        url = f"https://ark-funds.com/api/fund/holdings/{fund_id}"
        response = self.session.get(
            url,
            params={"fundHoldingData": json.dumps(data)},
            timeout=20,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        as_of = clean_text(soup.select_one(".b-char-date").get_text(" ", strip=True)) if soup.select_one(".b-char-date") else ""
        csv_link = next(
            (
                anchor.get("href")
                for anchor in soup.find_all("a", href=True)
                if anchor.get("href", "").lower().endswith(".csv")
            ),
            f"https://ark-funds.com/funds/{fund.lower()}/#hold",
        )
        rows = []
        for tr in soup.find_all("tr")[1:11]:
            cells = [clean_text(cell.get_text(" ", strip=True).replace("'", "")) for cell in tr.find_all("td")]
            if len(cells) >= 4 and cells[0] and cells[0] != "-":
                rows.append((cells[0], cells[1], cells[3]))
        if not rows:
            return None
        formatted = ", ".join(f"{ticker} {weight}" for ticker, _name, weight in rows[:10])
        return Evidence(
            title=f"ARK official {fund} top holdings",
            url=csv_link,
            source="ARK Invest",
            tier="official",
            category="ark",
            summary=f"{fund} official holdings {as_of}: top holdings include {formatted}.",
        )

    def collect_cathiesark_trades(self) -> list[Evidence]:
        trades: list[dict[str, str]] = []
        for fund in self.settings.ark_funds:
            trades.extend(self.fetch_cathiesark_fund_trades(fund))
        if not trades:
            return []
        buys = summarize_trades([trade for trade in trades if trade["action"].lower() == "buy"])
        sells = summarize_trades([trade for trade in trades if trade["action"].lower() == "sell"])
        repeated = summarize_repeated_trades(trades)
        trade_dates = trade_date_range(trades)
        evidence: list[Evidence] = []
        if buys:
            evidence.append(
                Evidence(
                    title="ARK secondary top buys",
                    url="https://www.cathiesark.com/arkk/trades",
                    source="Cathie's Ark",
                    tier="secondary",
                    category="ark",
                    summary=f"Secondary trade confirmation {trade_dates}: largest ARK buys include {buys}.",
                )
            )
        if sells:
            evidence.append(
                Evidence(
                    title="ARK secondary top sells",
                    url="https://www.cathiesark.com/arkk/trades",
                    source="Cathie's Ark",
                    tier="secondary",
                    category="ark",
                    summary=f"Secondary trade confirmation {trade_dates}: largest ARK sells include {sells}.",
                )
            )
        if repeated:
            evidence.append(
                Evidence(
                    title="ARK secondary repeated trade trends",
                    url="https://www.cathiesark.com/arkk/trades",
                    source="Cathie's Ark",
                    tier="secondary",
                    category="ark",
                    summary=f"Secondary trade confirmation {trade_dates}: repeated ARK trade tickers include {repeated}.",
                )
            )
        return evidence

    def fetch_cathiesark_fund_trades(self, fund: str) -> list[dict[str, str]]:
        url = f"https://www.cathiesark.com/{fund.lower()}/trades"
        try:
            html = self.session.get(url, timeout=20).text
            soup = BeautifulSoup(html, "html.parser")
            trades: list[dict[str, str]] = []
            for row in soup.find_all("tr")[:30]:
                cells = [clean_text(cell.get_text(" ", strip=True)) for cell in row.find_all("td")]
                if len(cells) < 4 or not re.search(r"\d{4}", cells[0]):
                    continue
                action = "Buy" if "Buy" in cells[2] else "Sell" if "Sell" in cells[2] else ""
                if not action:
                    continue
                trades.append(
                    {
                        "fund": fund,
                        "date": cells[0],
                        "ticker": cells[1],
                        "action": action,
                        "value": cells[3],
                    }
                )
            return trades
        except Exception:
            return []

    def collect_infra_signals(self, report_date: date) -> list[Evidence]:
        evidence: list[Evidence] = []
        for category, query in INFRA_QUERIES.items():
            for title, url, summary in INFRA_OFFICIAL_EVIDENCE.get(category, []):
                evidence.append(
                    Evidence(
                        title=title,
                        url=url,
                        source=hostname(url),
                        tier="official",
                        category=f"infra_{category}",
                        summary=summary,
                    )
                )
            official_query = query + " site:investor.nvidia.com OR site:ir.amd.com OR site:abc.xyz OR site:microsoft.com/en-us/investor OR site:ir.aboutamazon.com OR site:investor.oracle.com"
            evidence.extend(self.search_web(official_query, f"infra_{category}", limit=3, tier="official"))
            evidence.extend(self.search_secondary(query, f"infra_{category}", limit=2))
        return evidence

    def search_secondary(self, query: str, category: str, limit: int = 3) -> list[Evidence]:
        domain_filter = " OR ".join(f"site:{domain}" for domain in SECONDARY_DOMAINS)
        return self.search_web(f"{query} {domain_filter}", category, limit=limit, tier="secondary")

    def search_web(self, query: str, category: str, limit: int, tier: str) -> list[Evidence]:
        if self.settings.brave_search_api_key:
            results = self.search_brave(query, category, limit, tier)
        elif self.settings.serpapi_api_key:
            results = self.search_serpapi(query, category, limit, tier)
        else:
            results = self.search_duckduckgo(query, category, limit, tier)
        filtered = filter_by_tier(results, tier)
        if filtered:
            return filtered[:limit]
        return [
            Evidence(
                title="Search returned no matching source-tier results",
                url=f"https://duckduckgo.com/html/?q={quote_plus(query)}",
                source="Search",
                tier=tier,  # type: ignore[arg-type]
                category=category,
                summary=f"No {tier} results matched the configured source policy for query: {query}",
            )
        ]

    def search_brave(self, query: str, category: str, limit: int, tier: str) -> list[Evidence]:
        response = self.session.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": limit},
            headers={"X-Subscription-Token": self.settings.brave_search_api_key or ""},
            timeout=30,
        )
        response.raise_for_status()
        results = response.json().get("web", {}).get("results", [])[:limit]
        return [
            Evidence(
                title=item.get("title", "Search result"),
                url=item.get("url", ""),
                source=hostname(item.get("url", "")),
                tier=tier,  # type: ignore[arg-type]
                category=category,
                summary=clean_text(item.get("description", "")),
            )
            for item in results
            if item.get("url")
        ]

    def search_serpapi(self, query: str, category: str, limit: int, tier: str) -> list[Evidence]:
        response = self.session.get(
            "https://serpapi.com/search.json",
            params={"engine": "google", "q": query, "api_key": self.settings.serpapi_api_key},
            timeout=30,
        )
        response.raise_for_status()
        results = response.json().get("organic_results", [])[:limit]
        return [
            Evidence(
                title=item.get("title", "Search result"),
                url=item.get("link", ""),
                source=hostname(item.get("link", "")),
                tier=tier,  # type: ignore[arg-type]
                category=category,
                summary=clean_text(item.get("snippet", "")),
            )
            for item in results
            if item.get("link")
        ]

    def search_duckduckgo(self, query: str, category: str, limit: int, tier: str) -> list[Evidence]:
        url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        try:
            html = self.session.get(url, timeout=30).text
            soup = BeautifulSoup(html, "html.parser")
            results: list[Evidence] = []
            for result in soup.select(".result")[:limit]:
                link = result.select_one(".result__a")
                snippet = result.select_one(".result__snippet")
                if not link or not link.get("href"):
                    continue
                result_url = normalize_search_url(link.get("href", ""))
                results.append(
                    Evidence(
                        title=clean_text(link.get_text(" ", strip=True)),
                        url=result_url,
                        source=hostname(result_url),
                        tier=tier,  # type: ignore[arg-type]
                        category=category,
                        summary=clean_text(snippet.get_text(" ", strip=True) if snippet else ""),
                    )
                )
            return results
        except Exception as exc:
            return [
                Evidence(
                    title="Search warning",
                    url=url,
                    source="DuckDuckGo",
                    tier=tier,  # type: ignore[arg-type]
                    category=category,
                    summary=f"Could not complete search for '{query}': {exc}",
                )
            ]


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def hostname(url: str) -> str:
    match = re.search(r"https?://([^/]+)", url)
    return match.group(1).replace("www.", "") if match else "unknown"


def dedupe_evidence(items: Iterable[Evidence]) -> list[Evidence]:
    seen: set[str] = set()
    deduped: list[Evidence] = []
    for item in items:
        key = f"{item.title}:{item.url}" if item.url else f"{item.title}:{item.summary}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def compare_13f_holdings(
    latest: dict[str, int],
    previous: dict[str, int],
    latest_date: str,
    previous_date: str,
) -> list[Evidence]:
    latest_names = set(latest)
    previous_names = set(previous)
    new_names = sorted(latest_names - previous_names)[:10]
    exited_names = sorted(previous_names - latest_names)[:10]
    reductions = sorted(
        (
            (name, previous[name] - latest[name], previous[name], latest[name])
            for name in latest_names & previous_names
            if latest[name] < previous[name]
        ),
        key=lambda row: row[1],
        reverse=True,
    )[:10]
    url = OFFICIAL_URLS["nvidia_ir"]
    items: list[Evidence] = []
    if new_names:
        items.append(
            Evidence(
                title="NVIDIA 13F new positions",
                url=url + "#13f-new-positions",
                source="SEC EDGAR",
                tier="official",
                category="nvidia",
                summary=f"Comparing {latest_date} vs {previous_date}, new 13F positions include: {', '.join(new_names)}.",
            )
        )
    if exited_names:
        items.append(
            Evidence(
                title="NVIDIA 13F exited positions",
                url=url + "#13f-exited-positions",
                source="SEC EDGAR",
                tier="official",
                category="nvidia",
                summary=f"Comparing {latest_date} vs {previous_date}, exited 13F positions include: {', '.join(exited_names)}.",
            )
        )
    if reductions:
        formatted = ", ".join(f"{name} ({old:,} to {new:,} shares)" for name, _delta, old, new in reductions[:5])
        items.append(
            Evidence(
                title="NVIDIA 13F reduced positions",
                url=url + "#13f-reduced-positions",
                source="SEC EDGAR",
                tier="official",
                category="nvidia",
                summary=f"Comparing {latest_date} vs {previous_date}, largest reductions include: {formatted}.",
            )
        )
    return items


def strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_text(node: ET.Element, name: str) -> str:
    for child in node.iter():
        if strip_ns(child.tag) == name and child.text:
            return child.text.strip()
    return ""


def normalize_search_url(url: str) -> str:
    if url.startswith("//"):
        url = "https:" + url
    parsed = urlparse(url)
    if "duckduckgo.com" in parsed.netloc:
        params = parse_qs(parsed.query)
        if params.get("uddg"):
            return unquote(params["uddg"][0])
    return url


def parse_money(value: str) -> float:
    cleaned = value.replace("$", "").replace(",", "").strip().upper()
    multiplier = 1.0
    if cleaned.endswith("B"):
        multiplier = 1_000_000_000.0
        cleaned = cleaned[:-1]
    elif cleaned.endswith("M"):
        multiplier = 1_000_000.0
        cleaned = cleaned[:-1]
    elif cleaned.endswith("K"):
        multiplier = 1_000.0
        cleaned = cleaned[:-1]
    try:
        return float(cleaned) * multiplier
    except ValueError:
        return 0.0


def format_money(value: float) -> str:
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:.0f}"


def summarize_trades(trades: list[dict[str, str]]) -> str:
    by_ticker: dict[str, dict[str, object]] = {}
    for trade in trades:
        ticker = trade["ticker"]
        current = by_ticker.setdefault(ticker, {"value": 0.0, "funds": set(), "dates": set(), "count": 0})
        current["value"] = float(current["value"]) + parse_money(trade["value"])
        current["funds"].add(trade["fund"])  # type: ignore[union-attr]
        current["dates"].add(trade["date"])  # type: ignore[union-attr]
        current["count"] = int(current["count"]) + 1
    top = sorted(by_ticker.items(), key=lambda item: float(item[1]["value"]), reverse=True)[:5]
    return ", ".join(
        f"{ticker} {format_money(float(info['value']))} across {int(info['count'])} trade(s) in {', '.join(sorted(info['funds']))}"
        for ticker, info in top
    )


def summarize_repeated_trades(trades: list[dict[str, str]]) -> str:
    by_ticker: dict[str, dict[str, object]] = {}
    for trade in trades:
        ticker = trade["ticker"]
        current = by_ticker.setdefault(ticker, {"actions": set(), "funds": set(), "count": 0})
        current["actions"].add(trade["action"])  # type: ignore[union-attr]
        current["funds"].add(trade["fund"])  # type: ignore[union-attr]
        current["count"] = int(current["count"]) + 1
    repeated = sorted(
        ((ticker, info) for ticker, info in by_ticker.items() if int(info["count"]) >= 2),
        key=lambda item: int(item[1]["count"]),
        reverse=True,
    )[:6]
    return ", ".join(
        f"{ticker} ({int(info['count'])} trades, {', '.join(sorted(info['actions']))}, {', '.join(sorted(info['funds']))})"
        for ticker, info in repeated
    )


def trade_date_range(trades: list[dict[str, str]]) -> str:
    parsed: list[datetime] = []
    for trade in trades:
        try:
            parsed.append(datetime.strptime(trade["date"], "%b %d, %Y"))
        except ValueError:
            continue
    if not parsed:
        return "from the latest visible trade rows"
    start_dt = min(parsed)
    end_dt = max(parsed)
    start = f"{start_dt.strftime('%b')} {start_dt.day}, {start_dt.year}"
    end = f"{end_dt.strftime('%b')} {end_dt.day}, {end_dt.year}"
    if start == end:
        return f"for {end}"
    return f"from {start} to {end}"


def filter_by_tier(items: list[Evidence], tier: str) -> list[Evidence]:
    if tier == "official":
        allowed = OFFICIAL_DOMAINS
    elif tier == "secondary":
        allowed = SECONDARY_DOMAINS
    else:
        return items
    return [item for item in items if domain_allowed(hostname(item.url), allowed)]


def domain_allowed(domain: str, allowed_domains: list[str]) -> bool:
    return any(domain == allowed or domain.endswith("." + allowed) for allowed in allowed_domains)
