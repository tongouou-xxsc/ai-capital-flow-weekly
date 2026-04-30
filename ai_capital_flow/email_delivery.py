from __future__ import annotations

import argparse
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv


def send_email(subject: str, body: str, attachments: list[Path]) -> None:
    load_dotenv()
    smtp_host = required_env("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = required_env("SMTP_USER")
    smtp_password = required_env("SMTP_PASSWORD")
    email_from = os.getenv("EMAIL_FROM", smtp_user)
    email_to = required_env("EMAIL_TO")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = email_from
    message["To"] = email_to
    message.set_content(body)

    for path in attachments:
        if not path.exists():
            continue
        message.add_attachment(
            path.read_bytes(),
            maintype="text",
            subtype="markdown",
            filename=path.name,
        )

    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_password)
        smtp.send_message(message)


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Email weekly AI capital flow report.")
    parser.add_argument("--report", required=True, help="Path to reports/YYYY-MM-DD.md")
    parser.add_argument("--social-post", help="Path to social_posts/YYYY-MM-DD-xiaohongshu.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = Path(args.report)
    social_post = Path(args.social_post) if args.social_post else None
    attachments = [report]
    if social_post:
        attachments.append(social_post)

    body = (
        "Your weekly AI Capital Flow report is attached.\n\n"
        f"Report: {report.name}\n"
        f"Xiaohongshu draft: {social_post.name if social_post else 'not generated'}\n\n"
        "Risk reminder: this is research automation, not financial advice."
    )
    send_email(
        subject=f"AI Capital Flow Weekly - {report.stem}",
        body=body,
        attachments=attachments,
    )
    print("Email sent.")


if __name__ == "__main__":
    main()
