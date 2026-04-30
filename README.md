# AI Capital Flow Weekly

Weekly AI investment report generator.

It tracks:

- NVIDIA 13F / SEC filing changes and NVentures signals
- Cathie Wood / ARK Invest trades and ETF holdings
- AI infrastructure signals across GPU, AI cloud, data centers, storage, and energy

Reports are saved in:

- `reports/YYYY-MM-DD.md`
- `reports/YYYY-MM-DD.html`

Use the `.html` file if you want the easiest reading format.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set:

```text
SEC_USER_AGENT=AI Capital Flow Weekly your_email@example.com
```

This is required by the SEC for automated access. It is not a password.

## Run Locally

```bash
python3 scripts/run_report.py
```

Choose a report date:

```bash
python3 scripts/run_report.py --date 2026-04-30
```

For debugging only, allow a sparse report even if key sources fail:

```bash
python3 scripts/run_report.py --allow-sparse
```

## GitHub Actions

The workflow is at:

```text
.github/workflows/weekly-report.yml
```

It runs every Monday and commits the generated report back to GitHub.

Required GitHub Secret:

```text
SEC_USER_AGENT
```

Example value:

```text
AI Capital Flow Weekly your_email@example.com
```

Manual run:

```text
Actions → .github/workflows/weekly-report.yml → Run workflow
```

## Source Policy

Official sources first:

- NVIDIA Investor Relations / SEC filings
- NVentures
- ARK Invest fund holdings

Secondary sources only for confirmation:

- Cathie's Ark
- Fintel
- 13F.info
- Reuters / Barron's / Yahoo Finance

## Notes

This is research automation, not financial advice. Always verify filings, timestamps, liquidity, and valuation before investing.
