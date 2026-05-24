"""
reporters/email_reporter.py — Sends beautifully formatted HTML email reports.
"""

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from scrapers.base_scraper import RawTender

logger = logging.getLogger(__name__)


class EmailReporter:
    name = "Email"

    def __init__(self, settings):
        self.settings = settings

    async def send_report(self, tenders: list[RawTender]):
        if not tenders:
            return

        subject = (
            f"🔔 {len(tenders)} New Tech Tenders — "
            f"{datetime.now().strftime('%d %b %Y, %I:%M %p IST')}"
        )
        html_body = self._build_html(tenders)
        text_body = self._build_text(tenders)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.settings.EMAIL_SENDER
        msg["To"] = ", ".join(self.settings.EMAIL_RECIPIENTS)

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(self.settings.SMTP_HOST, self.settings.SMTP_PORT) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(self.settings.EMAIL_SENDER, self.settings.EMAIL_PASSWORD)
                smtp.sendmail(
                    self.settings.EMAIL_SENDER,
                    self.settings.EMAIL_RECIPIENTS,
                    msg.as_string(),
                )
            logger.info(f"Email sent to {len(self.settings.EMAIL_RECIPIENTS)} recipients")
            return True
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False

    def _build_html(self, tenders: list[RawTender]) -> str:
        now = datetime.now().strftime("%d %B %Y, %I:%M %p IST")

        rows = ""
        for i, t in enumerate(tenders, 1):
            badge_color = "#2563eb" if t.govt_type == "Central" else "#7c3aed"
            deadline_str = str(t.deadline) if t.deadline else "Not specified"
            value_str = t.tender_value or "Not disclosed"
            keywords_str = ", ".join(t.matched_keywords[:4]) if t.matched_keywords else "—"

            rows += f"""
            <tr style="background: {'#f8fafc' if i % 2 == 0 else 'white'}">
              <td style="padding:12px 8px; font-weight:600; color:#1e293b; border-bottom:1px solid #e2e8f0">
                <a href="{t.url}" style="color:#2563eb; text-decoration:none">{t.title}</a>
              </td>
              <td style="padding:12px 8px; color:#475569; border-bottom:1px solid #e2e8f0">{t.organization}</td>
              <td style="padding:12px 8px; border-bottom:1px solid #e2e8f0">
                <span style="background:{badge_color};color:white;padding:2px 8px;border-radius:12px;font-size:11px">
                  {t.govt_type}
                </span>
                <br><small style="color:#64748b">{t.state or 'Central'}</small>
              </td>
              <td style="padding:12px 8px; color:#475569; border-bottom:1px solid #e2e8f0; font-size:13px">{t.portal_source}</td>
              <td style="padding:12px 8px; color:#dc2626; border-bottom:1px solid #e2e8f0; font-weight:500">{deadline_str}</td>
              <td style="padding:12px 8px; color:#059669; border-bottom:1px solid #e2e8f0">{value_str}</td>
              <td style="padding:12px 8px; border-bottom:1px solid #e2e8f0; font-size:12px; color:#64748b">{keywords_str}</td>
            </tr>"""

        summary_html = ""
        for t in tenders[:5]:  # Show AI summaries for top 5
            if t.ai_summary:
                summary_html += f"""
                <div style="border:1px solid #e2e8f0;border-radius:8px;padding:16px;margin-bottom:12px;background:#f8fafc">
                  <h4 style="margin:0 0 8px 0;color:#1e293b">{t.title[:80]}</h4>
                  <p style="margin:0;color:#475569;font-size:13px;white-space:pre-line">{t.ai_summary}</p>
                </div>"""

        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin:0; padding:0; background:#f1f5f9; }}
    .container {{ max-width:900px; margin:20px auto; background:white; border-radius:12px; overflow:hidden; box-shadow:0 4px 24px rgba(0,0,0,0.1); }}
    .header {{ background:linear-gradient(135deg,#1e3a5f,#2563eb); padding:32px; color:white; }}
    .content {{ padding:24px; }}
    table {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th {{ background:#1e3a5f; color:white; padding:12px 8px; text-align:left; font-size:12px; text-transform:uppercase; letter-spacing:0.5px; }}
    .footer {{ background:#f8fafc; padding:16px 24px; text-align:center; color:#64748b; font-size:12px; border-top:1px solid #e2e8f0; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1 style="margin:0 0 8px 0;font-size:22px">🔍 AI Tender Monitor Report</h1>
      <p style="margin:0;opacity:0.85">{now} &nbsp;|&nbsp; {len(tenders)} new tech tenders found</p>
    </div>

    <div class="content">
      <h2 style="color:#1e293b;margin-top:0">📊 All Relevant Tenders</h2>
      <div style="overflow-x:auto">
        <table>
          <thead>
            <tr>
              <th>Tender Title</th>
              <th>Organization</th>
              <th>Type/State</th>
              <th>Portal</th>
              <th>Deadline</th>
              <th>Value</th>
              <th>Keywords</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
      </div>

      {'<h2 style="color:#1e293b;margin-top:32px">🤖 AI Summaries (Top 5)</h2>' + summary_html if summary_html else ''}
    </div>

    <div class="footer">
      Generated by AI Tender Monitor &nbsp;|&nbsp; 
      <a href="https://eprocure.gov.in" style="color:#2563eb">CPPP</a> &nbsp;|&nbsp;
      <a href="https://bidplus.gem.gov.in" style="color:#2563eb">GeM</a> &nbsp;|&nbsp;
      This is an automated report. Do not reply.
    </div>
  </div>
</body>
</html>"""

    def _build_text(self, tenders: list[RawTender]) -> str:
        now = datetime.now().strftime("%d %B %Y, %I:%M %p IST")
        lines = [
            f"AI Tender Monitor Report — {now}",
            f"Found {len(tenders)} new technology tenders",
            "=" * 60,
        ]
        for i, t in enumerate(tenders, 1):
            lines.extend([
                f"\n{i}. {t.title}",
                f"   Org: {t.organization}",
                f"   Source: {t.portal_source} ({t.govt_type})",
                f"   Deadline: {t.deadline or 'N/A'}",
                f"   Value: {t.tender_value or 'N/A'}",
                f"   Link: {t.url}",
            ])
        return "\n".join(lines)
