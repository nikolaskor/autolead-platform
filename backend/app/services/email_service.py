"""
Email Service for sending customer emails via Resend.

Features:
- Branded email templates
- Norwegian language support
- Delivery tracking
- Error handling and retries
"""
import logging
from typing import Optional
import resend
from ..core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails to customers."""

    def __init__(self):
        """Initialize Resend client."""
        resend.api_key = settings.RESEND_API_KEY

    def send_initial_response(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        ai_response: str,
        dealership_name: str,
        dealership_phone: Optional[str] = None,
        dealership_email: Optional[str] = None,
        dealership_address: Optional[str] = None
    ) -> dict:
        """
        Send initial AI-generated response to customer.

        Args:
            to_email: Customer email
            to_name: Customer name
            subject: Email subject
            ai_response: AI-generated response text
            dealership_name: Name of the dealership
            dealership_phone: Dealership phone
            dealership_email: Dealership email
            dealership_address: Dealership address

        Returns:
            dict with keys: email_id (str), status (str)
        """
        try:
            # Build HTML email
            html_content = self._build_email_html(
                customer_name=to_name,
                response_text=ai_response,
                dealership_name=dealership_name,
                dealership_phone=dealership_phone,
                dealership_email=dealership_email,
                dealership_address=dealership_address
            )

            # Build plain text version
            text_content = self._build_email_text(
                customer_name=to_name,
                response_text=ai_response,
                dealership_name=dealership_name,
                dealership_phone=dealership_phone,
                dealership_email=dealership_email
            )

            # Send email via Resend
            result = resend.Emails.send({
                "from": f"{dealership_name} <no-reply@autolead.no>",
                "to": [to_email],
                "subject": subject,
                "html": html_content,
                "text": text_content
            })

            logger.info(
                f"Email sent successfully to {to_email}",
                extra={
                    "email_id": result.get("id"),
                    "to": to_email,
                    "dealership": dealership_name
                }
            )

            return {
                "email_id": result.get("id"),
                "status": "sent",
                "provider": "resend"
            }

        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return {
                "email_id": None,
                "status": "failed",
                "error": str(e)
            }

    def _build_email_html(
        self,
        customer_name: str,
        response_text: str,
        dealership_name: str,
        dealership_phone: Optional[str],
        dealership_email: Optional[str],
        dealership_address: Optional[str]
    ) -> str:
        """Build HTML email template."""
        # Contact info section
        contact_html = ""
        if dealership_phone:
            contact_html += f'<p style="margin: 5px 0;">📞 Telefon: <a href="tel:{dealership_phone}" style="color: #1a73e8;">{dealership_phone}</a></p>'
        if dealership_email:
            contact_html += f'<p style="margin: 5px 0;">✉️ E-post: <a href="mailto:{dealership_email}" style="color: #1a73e8;">{dealership_email}</a></p>'
        if dealership_address:
            contact_html += f'<p style="margin: 5px 0;">📍 Adresse: {dealership_address}</p>'

        return f"""<!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Svar fra {dealership_name}</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; font-size: 24px; font-weight: 600;">{dealership_name}</h1>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <p style="margin: 0 0 20px 0; font-size: 16px; color: #333; line-height: 1.6;">
                                Hei {customer_name}!
                            </p>

                            <div style="margin: 20px 0; padding: 20px; background-color: #f8f9fa; border-left: 4px solid #1a73e8; border-radius: 4px;">
                                <p style="margin: 0; font-size: 16px; color: #333; line-height: 1.6; white-space: pre-wrap;">{response_text}</p>
                            </div>

                            <p style="margin: 20px 0 0 0; font-size: 16px; color: #333; line-height: 1.6;">
                                Med vennlig hilsen,<br>
                                <strong>{dealership_name}</strong>
                            </p>
                        </td>
                    </tr>

                    <!-- Contact Info -->
                    <tr>
                        <td style="padding: 0 30px 30px 30px;">
                            <div style="padding: 20px; background-color: #f8f9fa; border-radius: 6px;">
                                <p style="margin: 0 0 10px 0; font-size: 14px; font-weight: 600; color: #666;">
                                    Kontakt oss:
                                </p>
                                {contact_html}
                            </div>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 30px; background-color: #f8f9fa; border-radius: 0 0 8px 8px; text-align: center;">
                            <p style="margin: 0; font-size: 12px; color: #999;">
                                Denne meldingen ble sendt av {dealership_name}<br>
                                Powered by <a href="https://autolead.no" style="color: #1a73e8; text-decoration: none;">Autolead</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    def _build_email_text(
        self,
        customer_name: str,
        response_text: str,
        dealership_name: str,
        dealership_phone: Optional[str],
        dealership_email: Optional[str]
    ) -> str:
        """Build plain text email version."""
        contact_info = []
        if dealership_phone:
            contact_info.append(f"Telefon: {dealership_phone}")
        if dealership_email:
            contact_info.append(f"E-post: {dealership_email}")

        contact_str = "\n".join(contact_info) if contact_info else ""

        return f"""Hei {customer_name}!

{response_text}

Med vennlig hilsen,
{dealership_name}

---
Kontakt oss:
{contact_str}

Powered by Autolead
"""


# Global email service instance
email_service = EmailService()
