# 13F Analysis Agent

Python agent that fetches a fund's latest two 13F filings, detects portfolio changes, classifies holdings by AI infrastructure sector, and writes an investment report.

## What It Does

- Fetch latest 13F filings from SEC EDGAR
- Accept fund or manager name, such as `Situational Awareness LP`
- Optional `--cik` input when SEC name matching is imperfect
- Compare current vs previous quarter
- Detect new, increased, reduced, and closed positions
- Classify holdings into:
  - AI Chips
  - AI Cloud
  - Data Center
  - Power / Energy
  - Networking
  - Other
- Generate Markdown report at `reports/YYYY-MM-DD.md`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

```text
SEC_USER_AGENT=13F Analysis Agent your_email@example.com
```

SEC requires automated requests to include a real contact. This is not a password.

## Run

Analyze by fund name:

```bash
python3 scripts/run_13f_report.py --fund "Situational Awareness LP"
```

If name matching fails, use a SEC CIK:

```bash
python3 scripts/run_13f_report.py --fund "Situational Awareness LP" --cik 0000000000
```

Use a specific output date:

```bash
python3 scripts/run_13f_report.py --fund "Situational Awareness LP" --date 2026-05-03
```

## Report Format

```text
# 13F Analysis Report

## One-line Conclusion
Funds moved from ___ to ___.

## Key Changes
### Added
### Increased
### Reduced
### Closed

## Sector Shift

## Core Thesis

## Investment Implications

## Next Validation Points
```

## GitHub Actions

The workflow at `.github/workflows/weekly-report.yml` can run manually or quarterly.

Required GitHub Secret:

```text
SEC_USER_AGENT
```

Manual run:

```text
Actions → Quarterly 13F Analysis Report → Run workflow
```

Enter:

- `fund`: fund or manager name
- `cik`: optional SEC CIK

## Extensibility

The code is modular:

- `thirteenf_agent/sec_client.py`: SEC fetching and XML parsing
- `thirteenf_agent/analysis.py`: change detection and sector flow
- `thirteenf_agent/classifier.py`: sector classification rules
- `thirteenf_agent/report.py`: Markdown report output
- `thirteenf_agent/cli.py`: command-line interface

Future additions can include email sending, PDF export, and integration with a broader weekly report.

## Disclaimer

This is research automation, not financial advice. Always verify filings, timestamps, liquidity, and valuation before investing.
