# AI Capital Flow Weekly

Weekly Markdown report agent for tracking AI capital flows across:

- NVIDIA investment portfolio, NVentures, and 13F changes
- Cathie Wood / ARK Invest daily trades and ETF holdings
- AI infrastructure market signals across GPU, AI cloud, data centers, storage, and energy

The report is saved in two formats:

- `reports/YYYY-MM-DD.md`
- `reports/YYYY-MM-DD.html`

Xiaohongshu-ready drafts are saved as `social_posts/YYYY-MM-DD-xiaohongshu.md`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set:

- `SEC_USER_AGENT`: required for SEC access
- `OPENAI_API_KEY`: optional, improves the interpretation section

## Run

```bash
python3 scripts/run_report.py
```

By default, the run fails instead of publishing a thin report if key NVIDIA or ARK evidence is missing. For debugging only, you can allow a sparse report:

```bash
python3 scripts/run_report.py --allow-sparse
```

Create a Xiaohongshu draft from a generated report:

```bash
python3 scripts/create_xiaohongshu_post.py reports/2026-04-30.md
```

You can also choose a report date:

```bash
python3 scripts/run_report.py --date 2026-04-30
```

## Source Policy

Official sources are queried first:

- NVIDIA Investor Relations and SEC filings
- NVentures
- ARK Invest daily trades and ETF holdings

Secondary sources are used only for confirmation:

- Fintel
- 13F.info
- Cathie's Ark
- Reuters
- Barron's
- Yahoo Finance

Every collected evidence item stores a source URL and is rendered as a citation in the report. The report separates facts from interpretation in each major section.

## Scheduler: Cron

Run every Monday at 8:00 AM New York time:

```cron
0 8 * * 1 cd /path/to/ai-capital-flow-weekly && . .venv/bin/activate && python3 scripts/run_report.py && latest_report="$(ls -1 reports/*.md | sort | tail -n 1)" && python3 scripts/create_xiaohongshu_post.py "$latest_report"
```

On macOS, edit cron with:

```bash
crontab -e
```

Then paste the line above, replacing `/path/to/ai-capital-flow-weekly` with this project folder.

## Scheduler: GitHub Actions

A workflow is included at `.github/workflows/weekly-report.yml`.

To use it:

1. Push this folder to a GitHub repository.
2. Add repository secrets:
   - `OPENAI_API_KEY` if you want AI synthesis
   - `SEC_USER_AGENT`
3. Enable Actions.

The workflow runs weekly and commits the generated report back to the repository.
It also creates a Xiaohongshu draft in `social_posts/`.

## Email Delivery

Email delivery is optional and controlled by a GitHub Actions variable:

- Add repository variable `ENABLE_EMAIL` with value `true`
- Add repository secrets `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`, and `EMAIL_TO`

For Gmail, use:

- `SMTP_HOST`: `smtp.gmail.com`
- `SMTP_PORT`: `587`
- `SMTP_USER`: your Gmail address
- `SMTP_PASSWORD`: a Gmail app password, not your normal login password
- `EMAIL_FROM`: your Gmail address
- `EMAIL_TO`: the recipient email address

If `ENABLE_EMAIL` is not set to `true`, the weekly report still runs normally but skips the email step.
The email attaches only the HTML report, while Markdown reports and Xiaohongshu drafts remain saved in GitHub.

## Publishing to Xiaohongshu

The safe workflow is semi-automatic:

1. Let cron or GitHub Actions generate the weekly report.
2. Open the latest file in `social_posts/`.
3. Paste it into Xiaohongshu.
4. Add 1-3 screenshots or charts from the Markdown report if you want a more visual post.
5. Publish manually after checking the wording and risk disclaimer.

Fully automated posting to Xiaohongshu may violate platform rules unless you have an approved API or creator-tool integration. This project prepares a publish-ready draft but does not log in or post on your behalf.

## Extending Later

The project is intentionally split into small modules:

- `ai_capital_flow/sources.py`: data collection and source URLs
- `ai_capital_flow/analyzer.py`: synthesis and interpretation
- `ai_capital_flow/render.py`: Markdown output
- `ai_capital_flow/xiaohongshu.py`: Xiaohongshu draft output
- `ai_capital_flow/cli.py`: command-line entrypoint

Good next additions:

- Email delivery: add a `delivery/email.py` module that sends the Markdown file.
- PDF export: add `export/pdf.py` using Playwright or WeasyPrint.
- Dashboard: read report files from `reports/` and expose them through a small web app.
# ai-capital-flow-weekly
