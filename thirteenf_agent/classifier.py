from __future__ import annotations

SECTORS = [
    "AI Chips",
    "AI Cloud",
    "Data Center",
    "Power / Energy",
    "Networking",
    "Other",
]

KEYWORDS = {
    "AI Chips": [
        "NVIDIA",
        "ADVANCED MICRO",
        "AMD",
        "BROADCOM",
        "MARVELL",
        "TAIWAN SEMICONDUCTOR",
        "TSMC",
        "ARM",
        "INTEL",
        "MICRON",
        "LAM RESEARCH",
        "APPLIED MATERIALS",
        "ASML",
        "SYNOPSYS",
        "CADENCE",
    ],
    "AI Cloud": [
        "MICROSOFT",
        "AMAZON",
        "ALPHABET",
        "GOOGLE",
        "META",
        "ORACLE",
        "CLOUDFLARE",
        "SNOWFLAKE",
        "COREWEAVE",
        "NEBIUS",
    ],
    "Data Center": [
        "EQUINIX",
        "DIGITAL REALTY",
        "VERTIV",
        "SUPER MICRO",
        "DELL",
        "HEWLETT PACKARD",
        "HPE",
        "PURE STORAGE",
        "NETAPP",
        "SEAGATE",
        "WESTERN DIGITAL",
    ],
    "Power / Energy": [
        "VISTRA",
        "CONSTELLATION",
        "GE VERNOVA",
        "NEXTERA",
        "CAMECO",
        "OKLO",
        "NUScale",
        "AES",
        "DUKE ENERGY",
        "SOUTHERN CO",
        "PG&E",
        "EATON",
        "SCHNEIDER",
    ],
    "Networking": [
        "ARISTA",
        "CISCO",
        "JUNIPER",
        "CIENA",
        "LUMENTUM",
        "COHERENT",
        "CREDO",
        "BROADCOM",
    ],
}


def classify_holding(issuer: str, title: str = "") -> str:
    text = f"{issuer} {title}".upper()
    for sector, keywords in KEYWORDS.items():
        if any(keyword.upper() in text for keyword in keywords):
            return sector
    return "Other"
