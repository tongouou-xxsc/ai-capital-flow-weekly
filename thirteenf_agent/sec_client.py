from __future__ import annotations

import json
import re
import time
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from urllib.parse import quote_plus, urljoin

import requests

from .classifier import classify_holding
from .models import Filing, Holding


class SecClient:
    def __init__(self, user_agent: str) -> None:
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Accept": "application/json,text/xml,text/html,*/*",
            }
        )

    def resolve_cik(self, fund_name: str) -> tuple[str, str]:
        browse_match = self.resolve_cik_from_browse_edgar(fund_name)
        if browse_match:
            return browse_match

        url = "https://www.sec.gov/files/company_tickers.json"
        data = self._get_json(url)
        candidates = []
        query = normalize_name(fund_name)
        for item in data.values():
            title = item.get("title", "")
            score = SequenceMatcher(None, query, normalize_name(title)).ratio()
            if query in normalize_name(title):
                score += 0.3
            candidates.append((score, str(item["cik_str"]).zfill(10), title))
        candidates.sort(reverse=True)
        best_score, cik, matched_name = candidates[0]
        if best_score < 0.55:
            raise RuntimeError(
                f"Could not confidently resolve fund name '{fund_name}' to a SEC CIK. "
                "Use --cik with the manager CIK from SEC EDGAR."
            )
        return cik, matched_name

    def resolve_cik_from_browse_edgar(self, fund_name: str) -> tuple[str, str] | None:
        url = (
            "https://www.sec.gov/cgi-bin/browse-edgar"
            f"?company={quote_plus(fund_name)}&owner=exclude&action=getcompany&count=10&output=atom"
        )
        try:
            xml_text = self._get_text(url)
            root = ET.fromstring(xml_text.encode("utf-8"))
        except Exception:
            return None
        query = normalize_name(fund_name)
        candidates: list[tuple[float, str, str]] = []
        for entry in root.iter():
            if strip_ns(entry.tag) != "entry":
                continue
            title = ""
            cik = ""
            for child in entry.iter():
                tag = strip_ns(child.tag)
                if tag == "title" and child.text:
                    title = child.text.strip()
                elif tag == "cik" and child.text:
                    cik = child.text.strip().zfill(10)
            if not cik or not title:
                continue
            score = SequenceMatcher(None, query, normalize_name(title)).ratio()
            if query in normalize_name(title):
                score += 0.3
            candidates.append((score, cik, title))
        if not candidates:
            return None
        candidates.sort(reverse=True)
        score, cik, title = candidates[0]
        return (cik, title) if score >= 0.45 else None

    def fetch_recent_13f_filings(self, cik: str, limit: int = 2) -> list[Filing]:
        cik = cik.zfill(10)
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        data = self._get_json(url)
        recent = data.get("filings", {}).get("recent", {})
        rows = zip(
            recent.get("accessionNumber", []),
            recent.get("form", []),
            recent.get("filingDate", []),
            recent.get("reportDate", []),
            recent.get("primaryDocument", []),
        )
        filings: list[Filing] = []
        for accession, form, filing_date, report_date, primary_doc in rows:
            if not str(form).startswith("13F-HR"):
                continue
            filing_url = self.filing_document_url(cik, accession, primary_doc)
            filings.append(
                Filing(
                    accession=accession,
                    form=form,
                    filing_date=filing_date,
                    report_date=report_date,
                    primary_document=primary_doc,
                    url=filing_url,
                )
            )
            if len(filings) >= limit:
                break
        if len(filings) < 2:
            raise RuntimeError(f"SEC returned fewer than two 13F-HR filings for CIK {cik}.")
        return filings

    def fetch_holdings(self, cik: str, filing: Filing) -> list[Holding]:
        cik_int = str(int(cik))
        accession_no_dash = filing.accession.replace("-", "")
        base_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_no_dash}/"
        index = self._get_json(urljoin(base_url, "index.json"))
        info_file = find_information_table(index)
        if not info_file:
            raise RuntimeError(f"No information table XML found for filing {filing.accession}.")
        xml_text = self._get_text(urljoin(base_url, info_file))
        return parse_information_table(xml_text)

    def filing_document_url(self, cik: str, accession: str, primary_doc: str) -> str:
        return (
            f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
            f"{accession.replace('-', '')}/{primary_doc}"
        )

    def _get_json(self, url: str) -> dict:
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        time.sleep(0.12)
        return response.json()

    def _get_text(self, url: str) -> str:
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        time.sleep(0.12)
        return response.text


def find_information_table(index_json: dict) -> str | None:
    files = index_json.get("directory", {}).get("item", [])
    for item in files:
        name = item.get("name", "")
        lower = name.lower()
        if lower.endswith(".xml") and "primary" not in lower and "xsl" not in lower:
            return name
    for item in files:
        name = item.get("name", "")
        if name.lower().endswith(".txt"):
            return name
    return None


def parse_information_table(xml_text: str) -> list[Holding]:
    if "<XML>" in xml_text.upper():
        xml_text = extract_xml_fragment(xml_text)
    root = ET.fromstring(xml_text.encode("utf-8"))
    holdings: list[Holding] = []
    for info in root.iter():
        if strip_ns(info.tag) != "infoTable":
            continue
        issuer = child_text(info, "nameOfIssuer")
        cusip = child_text(info, "cusip")
        title = child_text(info, "titleOfClass")
        value_text = child_text(info, "value")
        shares_text = child_text(info, "sshPrnamt")
        if not issuer:
            continue
        value_usd = parse_int(value_text) * 1000
        shares = parse_int(shares_text)
        holdings.append(
            Holding(
                issuer=clean_spaces(issuer).upper(),
                cusip=clean_spaces(cusip).upper(),
                title=clean_spaces(title).upper(),
                value_usd=value_usd,
                shares=shares,
                sector=classify_holding(issuer, title),
            )
        )
    return holdings


def extract_xml_fragment(text: str) -> str:
    match = re.search(r"<XML>(.*?)</XML>", text, flags=re.I | re.S)
    if not match:
        return text
    return match.group(1).strip()


def strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_text(node: ET.Element, name: str) -> str:
    for child in node.iter():
        if strip_ns(child.tag) == name and child.text:
            return child.text.strip()
    return ""


def parse_int(value: str) -> int:
    try:
        return int(float((value or "0").replace(",", "")))
    except ValueError:
        return 0


def clean_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_name(value: str) -> str:
    value = value.upper()
    value = re.sub(r"[^A-Z0-9 ]+", " ", value)
    value = re.sub(r"\b(LP|LLC|LTD|INC|CORP|CO|THE|ADVISORS|MANAGEMENT)\b", " ", value)
    return clean_spaces(value)
