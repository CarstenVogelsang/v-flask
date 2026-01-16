"""Abstract Email Service Interface for V-Flask.

Provides a base interface for email services that can be implemented
by different providers (Brevo, SendGrid, AWS SES, etc.).

Usage:
    from v_flask.services import EmailServiceInterface, EmailResult
    from v_flask.services.brevo_service import BrevoService

    # Get configured email service
    email_service = BrevoService()

    # Check if configured
    if email_service.is_configured:
        result = email_service.send_email(
            to_email='user@example.com',
            to_name='John Doe',
            subject='Hello',
            html_content='<p>Hello World</p>'
        )
        if result.success:
            print(f'Sent! Message ID: {result.message_id}')
        else:
            print(f'Failed: {result.error}')
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class EmailResult:
    """Result of an email send operation.

    Attributes:
        success: Whether the email was sent successfully.
        message_id: Provider-specific message ID (if successful).
        error: Error message (if failed).
    """
    success: bool
    message_id: str | None = None
    error: str | None = None


class QuotaExceededError(Exception):
    """Raised when daily email quota is exceeded."""
    pass


class EmailServiceInterface(ABC):
    """Abstract base class for email services.

    Subclasses must implement:
        - is_configured (property)
        - send_email()

    Default implementations are provided for convenience methods.
    """

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the email service is configured and ready to send.

        Returns:
            True if all required configuration (API keys, etc.) is present.
        """
        ...

    @abstractmethod
    def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        text_content: str | None = None
    ) -> EmailResult:
        """Send an email.

        Args:
            to_email: Recipient email address.
            to_name: Recipient display name.
            subject: Email subject line.
            html_content: HTML body content.
            text_content: Optional plain text body.

        Returns:
            EmailResult with success status and message_id or error.
        """
        ...

    def send_fragebogen_einladung(
        self,
        to_email: str,
        to_name: str,
        fragebogen_titel: str,
        magic_url: str,
        absender_name: str = 'V-Flask'
    ) -> EmailResult:
        """Send questionnaire invitation with magic-link.

        Default implementation sends a simple HTML email.
        Override in subclasses for branded templates.

        Args:
            to_email: Recipient email address.
            to_name: Recipient display name.
            fragebogen_titel: Title of the questionnaire.
            magic_url: Full URL for direct access (no login required).
            absender_name: Sender display name for greeting.

        Returns:
            EmailResult
        """
        subject = f'Einladung: {fragebogen_titel}'

        html_content = f'''
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>{fragebogen_titel}</h2>

            <p>Guten Tag {to_name},</p>

            <p>Sie wurden eingeladen, an einem Fragebogen teilzunehmen.</p>

            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px;
                        margin: 20px 0; text-align: center;">
                <a href="{magic_url}"
                   style="display: inline-block; background-color: #10b981; color: white;
                          padding: 14px 28px; text-decoration: none; border-radius: 4px;
                          font-weight: bold; font-size: 16px;">
                    Fragebogen starten
                </a>
            </div>

            <p style="color: #666;">
                <strong>Hinweis:</strong> Dieser Link ist persönlich und nur für Sie bestimmt.
                Eine Anmeldung ist nicht erforderlich.
            </p>

            <p style="color: #666; font-size: 14px; margin-top: 30px;">
                Mit freundlichen Grüßen<br>
                {absender_name}
            </p>
        </body>
        </html>
        '''

        text_content = f'''
{fragebogen_titel}

Guten Tag {to_name},

Sie wurden eingeladen, an einem Fragebogen teilzunehmen.

Klicken Sie hier, um den Fragebogen zu starten:
{magic_url}

Hinweis: Dieser Link ist persönlich und nur für Sie bestimmt.
Eine Anmeldung ist nicht erforderlich.

Mit freundlichen Grüßen
{absender_name}
        '''

        return self.send_email(to_email, to_name, subject, html_content, text_content)

    def send_fragebogen_erinnerung(
        self,
        to_email: str,
        to_name: str,
        fragebogen_titel: str,
        magic_url: str,
        absender_name: str = 'V-Flask'
    ) -> EmailResult:
        """Send questionnaire reminder with magic-link.

        Default implementation sends a simple HTML email.
        Override in subclasses for branded templates.

        Args:
            to_email: Recipient email address.
            to_name: Recipient display name.
            fragebogen_titel: Title of the questionnaire.
            magic_url: Full URL for direct access (no login required).
            absender_name: Sender display name for greeting.

        Returns:
            EmailResult
        """
        subject = f'Erinnerung: {fragebogen_titel}'

        html_content = f'''
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2>Erinnerung: {fragebogen_titel}</h2>

            <p>Guten Tag {to_name},</p>

            <p>wir möchten Sie daran erinnern, dass Sie noch an unserem
            Fragebogen teilnehmen können.</p>

            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px;
                        margin: 20px 0; text-align: center;">
                <a href="{magic_url}"
                   style="display: inline-block; background-color: #10b981; color: white;
                          padding: 14px 28px; text-decoration: none; border-radius: 4px;
                          font-weight: bold; font-size: 16px;">
                    Fragebogen fortsetzen
                </a>
            </div>

            <p style="color: #666; font-size: 14px; margin-top: 30px;">
                Mit freundlichen Grüßen<br>
                {absender_name}
            </p>
        </body>
        </html>
        '''

        text_content = f'''
Erinnerung: {fragebogen_titel}

Guten Tag {to_name},

wir möchten Sie daran erinnern, dass Sie noch an unserem
Fragebogen teilnehmen können.

Klicken Sie hier, um den Fragebogen fortzusetzen:
{magic_url}

Mit freundlichen Grüßen
{absender_name}
        '''

        return self.send_email(to_email, to_name, subject, html_content, text_content)

    def send_test_email(self, to_email: str, to_name: str) -> EmailResult:
        """Send a test email to verify configuration.

        Args:
            to_email: Recipient email address.
            to_name: Recipient display name.

        Returns:
            EmailResult with success status.
        """
        from datetime import datetime

        timestamp = datetime.now().strftime('%d.%m.%Y %H:%M:%S')

        subject = f'[TEST] Email Service Test ({timestamp})'

        html_content = f'''
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #10b981;">✓ Email Service Test erfolgreich</h2>

            <p>Guten Tag {to_name},</p>

            <p>Dies ist eine Test-E-Mail zur Überprüfung der Email-Service-Konfiguration.</p>

            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Zeitstempel:</strong> {timestamp}</p>
                <p><strong>Empfänger:</strong> {to_email}</p>
            </div>

            <p style="color: #10b981;">
                <strong>✓ Die Konfiguration funktioniert korrekt.</strong>
            </p>
        </body>
        </html>
        '''

        text_content = f'''
Email Service Test erfolgreich

Guten Tag {to_name},

Dies ist eine Test-E-Mail zur Überprüfung der Email-Service-Konfiguration.

Zeitstempel: {timestamp}
Empfänger: {to_email}

Die Konfiguration funktioniert korrekt.
        '''

        return self.send_email(to_email, to_name, subject, html_content, text_content)


class NullEmailService(EmailServiceInterface):
    """Null implementation that logs emails but doesn't send them.

    Useful for development and testing when no email provider is configured.
    """

    @property
    def is_configured(self) -> bool:
        """Always returns True (no configuration needed)."""
        return True

    def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        text_content: str | None = None
    ) -> EmailResult:
        """Log the email instead of sending it.

        In development mode, logs email details to the Flask logger.

        Returns:
            EmailResult with success=True and a fake message_id.
        """
        from flask import current_app

        current_app.logger.info(
            f"[NullEmailService] Would send email:\n"
            f"  To: {to_name} <{to_email}>\n"
            f"  Subject: {subject}\n"
            f"  HTML Length: {len(html_content)} chars"
        )

        return EmailResult(
            success=True,
            message_id=f"null-{to_email}-{hash(subject)}"
        )
