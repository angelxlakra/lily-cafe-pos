"""
Email utility for sending inventory reports via SMTP.
Uses Python's built-in smtplib - no additional dependencies required.
"""

import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(subject: str, html_body: str, recipients: List[str]) -> bool:
    """
    Send an HTML email via SMTP (Gmail STARTTLS on port 587).
    Returns True on success, False on failure. Never raises.
    """
    if not recipients:
        logger.warning("No email recipients configured, skipping send")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_SENDER_EMAIL
        msg["To"] = ", ".join(recipients)
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_SENDER_EMAIL, recipients, msg.as_string())

        logger.info(f"Inventory report email sent to {recipients}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


def build_inventory_report_html(
    low_stock_items: List[Dict[str, Any]],
    changes: List[Dict[str, Any]],
    recorded_by: str,
    timestamp: str,
) -> str:
    """
    Build an inline-CSS HTML email with two sections:
    - Low Stock Alert (red header) - all items below threshold
    - Daily Count Changes (blue header) - items changed in this count
    """
    # Low stock section
    if low_stock_items:
        low_stock_rows = ""
        for item in low_stock_items:
            pct = item["percentage_remaining"]
            if pct < 25:
                row_color = "#fee2e2"  # red
            elif pct < 50:
                row_color = "#ffedd5"  # orange
            elif pct < 75:
                row_color = "#fef9c3"  # yellow
            else:
                row_color = "#ffffff"

            low_stock_rows += f"""
            <tr style="background-color: {row_color};">
                <td style="padding: 8px; border: 1px solid #ddd;">{item["name"]}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{item["category_name"]}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{item["current_quantity"]} {item["unit"]}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{item["min_threshold"]} {item["unit"]}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{pct:.0f}%</td>
            </tr>"""

        low_stock_section = f"""
        <div style="margin-bottom: 24px;">
            <h2 style="color: #dc2626; margin-bottom: 12px;">Low Stock Alert ({len(low_stock_items)} items)</h2>
            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <thead>
                    <tr style="background-color: #fecaca;">
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Item</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Category</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Current</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Min Threshold</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">% Remaining</th>
                    </tr>
                </thead>
                <tbody>{low_stock_rows}
                </tbody>
            </table>
        </div>"""
    else:
        low_stock_section = """
        <div style="margin-bottom: 24px; padding: 16px; background-color: #d1fae5; border-radius: 8px; text-align: center;">
            <h2 style="color: #059669; margin: 0;">All items adequately stocked</h2>
        </div>"""

    # Changes section
    changes_rows = ""
    for change in changes:
        diff = change["difference"]
        if diff > 0:
            diff_color = "#16a34a"  # green
            diff_str = f"+{diff}"
        else:
            diff_color = "#dc2626"  # red
            diff_str = str(diff)

        changes_rows += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{change["item_name"]}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{change["previous_quantity"]}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{change["new_quantity"]}</td>
                <td style="padding: 8px; border: 1px solid #ddd; color: {diff_color}; font-weight: bold;">{diff_str}</td>
            </tr>"""

    changes_section = f"""
        <div style="margin-bottom: 24px;">
            <h2 style="color: #2563eb; margin-bottom: 12px;">Daily Count Changes ({len(changes)} items)</h2>
            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <thead>
                    <tr style="background-color: #bfdbfe;">
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Item</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Previous</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">New</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Difference</th>
                    </tr>
                </thead>
                <tbody>{changes_rows}
                </tbody>
            </table>
        </div>"""

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; color: #333;">
        <h1 style="color: #1e293b; border-bottom: 2px solid #e2e8f0; padding-bottom: 12px;">
            {settings.RESTAURANT_NAME} - Inventory Report
        </h1>
        <p style="color: #64748b; margin-bottom: 20px;">
            Recorded by <strong>{recorded_by}</strong> on {timestamp}
        </p>
        {low_stock_section}
        {changes_section}
        <p style="color: #94a3b8; font-size: 12px; margin-top: 24px; border-top: 1px solid #e2e8f0; padding-top: 12px;">
            This is an automated report from {settings.RESTAURANT_NAME} POS System.
        </p>
    </body>
    </html>"""


def send_inventory_report(
    low_stock_items: List[Dict[str, Any]],
    changes: List[Dict[str, Any]],
    recorded_by: str,
) -> None:
    """
    Entry point for BackgroundTasks. Builds HTML report and sends email.
    Wrapped in try/except to never crash the background worker.
    """
    try:
        recipients = settings.INVENTORY_REPORT_EMAILS
        if not recipients:
            logger.warning("INVENTORY_REPORT_EMAILS not configured, skipping inventory report email")
            return

        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        html_body = build_inventory_report_html(low_stock_items, changes, recorded_by, timestamp)

        subject = f"Inventory Report - {settings.RESTAURANT_NAME}"
        if low_stock_items:
            subject = f"[LOW STOCK] {subject} ({len(low_stock_items)} items)"

        send_email(subject, html_body, recipients)
    except Exception as e:
        logger.error(f"Error in send_inventory_report background task: {e}")
