"""Brevo (formerly Sendinblue) Email Service Implementation.

Uses Brevo REST API for sending transactional emails.
Includes rate limiting for Brevo Free Plan (300 emails/day).

Configuration is stored in the Config model:
    - brevo_api_key: Brevo API key (required)
    - brevo_sender_email: Sender email address
    - brevo_sender_name: Sender display name
    - brevo_daily_limit: Daily email limit (default: 300)

Usage:
    from v_flask.services import get_email_service

    email_service = get_email_service()
    if email_service.is_configured:
        result = email_service.send_email(...)
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import requests

from v_flask.services.email_service import (
    EmailResult,
    EmailServiceInterface,
    QuotaExceededError,
)

if TYPE_CHECKING:
    pass


class BrevoService(EmailServiceInterface):
    """Brevo implementation of EmailServiceInterface.

    Features:
        - Transactional email sending via REST API
        - Daily quota management (for free tier)
        - Configuration stored in database (Config model)
        - Automatic portal URL detection in debug mode
    """

    BREVO_API_URL = 'https://api.brevo.com/v3/smtp/email'

    def __init__(self) -> None:
        """Initialize the Brevo service."""
        self._api_key: str | None = None
        self._sender_email: str | None = None
        self._sender_name: str | None = None
        self._portal_base_url: str | None = None

    def _load_config(self) -> None:
        """Load configuration from database.

        Reads config values from the Config model. Falls back to
        environment-based defaults if not configured.
        """
        from flask import current_app, has_request_context, request

        from v_flask.models import Config

        self._api_key = Config.get_value('brevo_api_key')
        self._sender_email = Config.get_value('brevo_sender_email', 'noreply@example.com')
        self._sender_name = Config.get_value('brevo_sender_name', 'V-Flask App')

        # Portal URL: Dynamic in dev mode, Config in production
        configured_url = Config.get_value('portal_base_url', '')

        if current_app.debug and has_request_context():
            # In dev mode: Use current request URL
            self._portal_base_url = request.host_url.rstrip('/')
        elif configured_url:
            self._portal_base_url = configured_url.rstrip('/')
        else:
            self._portal_base_url = 'https://example.com'

    @property
    def is_configured(self) -> bool:
        """Check if Brevo is configured with an API key.

        Returns:
            True if brevo_api_key is set in Config.
        """
        self._load_config()
        return bool(self._api_key)

    @property
    def portal_base_url(self) -> str:
        """Get the portal base URL for link generation.

        Returns:
            The configured portal URL or default.
        """
        if self._portal_base_url is None:
            self._load_config()
        return self._portal_base_url or 'https://example.com'

    # =========================================================================
    # Quota Management
    # =========================================================================

    def _reset_quota_if_new_day(self) -> None:
        """Reset the daily quota counter if a new day has started."""
        from v_flask.models import Config

        today_str = date.today().isoformat()
        last_reset = Config.get_value('brevo_last_reset_date', '')

        if last_reset != today_str:
            Config.set_value('brevo_emails_sent_today', '0')
            Config.set_value('brevo_last_reset_date', today_str)

    def _check_quota(self) -> bool:
        """Check if quota is available (without incrementing).

        Returns:
            True if email can be sent.

        Raises:
            QuotaExceededError: If daily limit is reached.
        """
        from v_flask.models import Config

        self._reset_quota_if_new_day()

        daily_limit = int(Config.get_value('brevo_daily_limit', '300'))
        sent_today = int(Config.get_value('brevo_emails_sent_today', '0'))

        if sent_today >= daily_limit:
            raise QuotaExceededError(
                f'Tägliches E-Mail-Limit erreicht ({daily_limit} E-Mails). '
                f'Bitte warten Sie bis morgen oder erhöhen Sie das Limit.'
            )
        return True

    def _increment_quota(self) -> None:
        """Increment the sent counter after successful send."""
        from v_flask.models import Config

        sent_today = int(Config.get_value('brevo_emails_sent_today', '0'))
        Config.set_value('brevo_emails_sent_today', str(sent_today + 1))

    def get_remaining_quota(self) -> int:
        """Get the number of remaining emails for today.

        Returns:
            Number of emails that can still be sent today.
        """
        from v_flask.models import Config

        self._reset_quota_if_new_day()
        daily_limit = int(Config.get_value('brevo_daily_limit', '300'))
        sent_today = int(Config.get_value('brevo_emails_sent_today', '0'))
        return max(0, daily_limit - sent_today)

    def get_quota_info(self) -> dict:
        """Get quota information for display in admin UI.

        Returns:
            Dict with quota details:
                - daily_limit: Max emails per day
                - sent_today: Emails sent today
                - remaining: Emails remaining
                - percent_used: Percentage of quota used
                - is_low: True if <10% remaining
                - is_exhausted: True if no quota left
        """
        from v_flask.models import Config

        self._reset_quota_if_new_day()
        daily_limit = int(Config.get_value('brevo_daily_limit', '300'))
        sent_today = int(Config.get_value('brevo_emails_sent_today', '0'))
        remaining = max(0, daily_limit - sent_today)
        percent_used = (sent_today / daily_limit * 100) if daily_limit > 0 else 0

        return {
            'daily_limit': daily_limit,
            'sent_today': sent_today,
            'remaining': remaining,
            'percent_used': min(100, percent_used),
            'is_low': remaining < (daily_limit * 0.1),
            'is_exhausted': remaining == 0
        }

    # =========================================================================
    # Email Sending
    # =========================================================================

    def send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        text_content: str | None = None
    ) -> EmailResult:
        """Send an email via Brevo API.

        Args:
            to_email: Recipient email address.
            to_name: Recipient display name.
            subject: Email subject line.
            html_content: HTML body content.
            text_content: Optional plain text body.

        Returns:
            EmailResult with success status and message_id or error.
        """
        self._load_config()

        if not self._api_key:
            return EmailResult(success=False, error='Brevo API-Key nicht konfiguriert')

        # Check quota before sending
        try:
            self._check_quota()
        except QuotaExceededError as e:
            return EmailResult(success=False, error=str(e))

        headers = {
            'accept': 'application/json',
            'api-key': self._api_key,
            'content-type': 'application/json'
        }

        payload = {
            'sender': {
                'name': self._sender_name,
                'email': self._sender_email
            },
            'to': [
                {'email': to_email, 'name': to_name}
            ],
            'subject': subject,
            'htmlContent': html_content
        }

        if text_content:
            payload['textContent'] = text_content

        try:
            response = requests.post(
                self.BREVO_API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 201:
                self._increment_quota()
                data = response.json()
                return EmailResult(success=True, message_id=data.get('messageId'))
            else:
                error_msg = f'Brevo API Fehler: {response.status_code}'
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                except Exception:
                    pass
                return EmailResult(success=False, error=error_msg)

        except requests.Timeout:
            return EmailResult(success=False, error='Brevo API Timeout')
        except requests.RequestException as e:
            return EmailResult(success=False, error=f'Netzwerkfehler: {str(e)}')

    # =========================================================================
    # API Status
    # =========================================================================

    def check_api_status(self) -> dict:
        """Check Brevo API status and account info.

        Returns:
            Dict with API status information:
                - success: True if API is reachable
                - configured: True if API key is set
                - email: Account email (if successful)
                - company_name: Account company (if successful)
                - plan: Account plan type (if successful)
                - error: Error message (if failed)
        """
        self._load_config()

        if not self._api_key:
            return {
                'success': False,
                'error': 'API-Key nicht konfiguriert',
                'configured': False
            }

        headers = {
            'accept': 'application/json',
            'api-key': self._api_key
        }

        try:
            response = requests.get(
                'https://api.brevo.com/v3/account',
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                plan_data = data.get('plan', [{}])
                plan = plan_data[0] if plan_data else {}
                return {
                    'success': True,
                    'configured': True,
                    'email': data.get('email', '-'),
                    'company_name': data.get('companyName', '-'),
                    'plan': plan.get('type', 'unknown'),
                    'credits': plan.get('credits', 0)
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'error': 'Ungültiger API-Key',
                    'configured': True
                }
            else:
                return {
                    'success': False,
                    'error': f'API-Fehler: {response.status_code}',
                    'configured': True
                }

        except requests.Timeout:
            return {
                'success': False,
                'error': 'Timeout bei API-Anfrage',
                'configured': True
            }
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f'Netzwerkfehler: {str(e)}',
                'configured': True
            }


# =============================================================================
# Singleton and Factory
# =============================================================================

_email_service: EmailServiceInterface | None = None


def get_email_service() -> EmailServiceInterface:
    """Get the configured email service.

    Returns:
        BrevoService if configured, NullEmailService otherwise.

    Usage:
        from v_flask.services import get_email_service

        service = get_email_service()
        result = service.send_email(...)
    """
    global _email_service

    if _email_service is None:
        brevo = BrevoService()
        if brevo.is_configured:
            _email_service = brevo
        else:
            from v_flask.services.email_service import NullEmailService
            _email_service = NullEmailService()

    return _email_service


def reset_email_service() -> None:
    """Reset the email service singleton.

    Call this if configuration changes at runtime.
    """
    global _email_service
    _email_service = None
