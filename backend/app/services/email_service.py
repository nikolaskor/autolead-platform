"""
Email Service for sending customer emails via SendGrid.

Features:
- Branded email templates
- Norwegian language support
- Delivery tracking
- Error handling and retries
- Multi-tenant support with Reply-To
"""
import html
import logging
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, ReplyTo
from ..core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails to customers."""

    def __init__(self):
        """Initialize SendGrid client."""
        if not settings.SENDGRID_API_KEY:
            raise ValueError(
                "SENDGRID_API_KEY is not set. Please provide a valid API key in your configuration."
            )
        self.client = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)

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

        Multi-tenant setup:
        - From: Shared domain (no-reply@autolead.no)
        - From Name: Dealership name
        - Reply-To: Dealership email

        Args:
            to_email: Customer email
            to_name: Customer name
            subject: Email subject
            ai_response: AI-generated response text
            dealership_name: Name of the dealership
            dealership_phone: Dealership phone
            dealership_email: Dealership email (used for Reply-To)
            dealership_address: Dealership address

        Returns:
            dict: On success, contains keys:
                - email_id (str or None): The ID of the sent email from SendGrid.
                - status (str): "sent" on success.
                - provider (str): The email provider used ("sendgrid").
                - status_code (int): The HTTP status code from the provider.
            On failure, contains keys:
                - email_id (None)
                - status (str): "failed"
                - error (str): Error message.
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

            # Create SendGrid email message
            message = Mail(
                from_email=Email("no-reply@autolead.no", dealership_name),
                to_emails=To(to_email, to_name),
                subject=subject,
                plain_text_content=Content("text/plain", text_content),
                html_content=Content("text/html", html_content)
            )

            # Set Reply-To to dealership email (multi-tenant isolation)
            if dealership_email:
                message.reply_to = ReplyTo(dealership_email, dealership_name)

            # Send email via SendGrid
            response = self.client.send(message)

            logger.info(
                f"Email sent successfully to {to_email}",
                extra={
                    "status_code": response.status_code,
                    "to": to_email,
                    "dealership": dealership_name,
                    "reply_to": dealership_email
                }
            )

            return {
                "email_id": response.headers.get("X-Message-Id"),
                "status": "sent",
                "provider": "sendgrid",
                "status_code": response.status_code
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
        """Build HTML email template with proper HTML escaping to prevent XSS."""
        # Escape all user-provided content
        customer_name_escaped = html.escape(customer_name)
        response_text_escaped = html.escape(response_text)
        dealership_name_escaped = html.escape(dealership_name)
        
        # Contact info section with escaped values
        contact_html = ""
        if dealership_phone:
            dealership_phone_escaped = html.escape(dealership_phone)
            contact_html += f'<p style="margin: 5px 0;">📞 Telefon: <a href="tel:{dealership_phone_escaped}" style="color: #1a73e8;">{dealership_phone_escaped}</a></p>'
        if dealership_email:
            dealership_email_escaped = html.escape(dealership_email)
            contact_html += f'<p style="margin: 5px 0;">✉️ E-post: <a href="mailto:{dealership_email_escaped}" style="color: #1a73e8;">{dealership_email_escaped}</a></p>'
        if dealership_address:
            dealership_address_escaped = html.escape(dealership_address)
            contact_html += f'<p style="margin: 5px 0;">📍 Adresse: {dealership_address_escaped}</p>'

        return f"""<!DOCTYPE html>
<html lang="no">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Svar fra {dealership_name_escaped}</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; font-size: 24px; font-weight: 600;">{dealership_name_escaped}</h1>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <p style="margin: 0 0 20px 0; font-size: 16px; color: #333; line-height: 1.6;">
                                Hei {customer_name_escaped}!
                            </p>

                            <div style="margin: 20px 0; padding: 20px; background-color: #f8f9fa; border-left: 4px solid #1a73e8; border-radius: 4px;">
                                <p style="margin: 0; font-size: 16px; color: #333; line-height: 1.6; white-space: pre-wrap;">{response_text_escaped}</p>
                            </div>

                            <p style="margin: 20px 0 0 0; font-size: 16px; color: #333; line-height: 1.6;">
                                Med vennlig hilsen,<br>
                                <strong>{dealership_name_escaped}</strong>
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
                                Denne meldingen ble sendt av {dealership_name_escaped}<br>
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
