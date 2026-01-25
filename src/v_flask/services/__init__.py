"""
v-flask Services

Logging, Email, Two-Factor Authentication und andere Dienste.

Usage:
    # Logging
    from v_flask.services import log_event, log_hoch, log_mittel, log_kritisch

    log_event('projekt', 'erstellt', 'Projekt "Website" erstellt')
    log_hoch('projekt', 'gelöscht', 'Projekt wurde gelöscht')

    # Email Service
    from v_flask.services import get_email_service, EmailResult

    email_service = get_email_service()
    if email_service.is_configured:
        result = email_service.send_email(
            to_email='user@example.com',
            to_name='Max Mustermann',
            subject='Hallo',
            html_content='<p>Hallo Welt</p>'
        )
        if result.success:
            print(f'Gesendet! Message ID: {result.message_id}')

    # Two-Factor Authentication (2FA)
    from v_flask.services import TwoFAService

    # Generate secret and QR code
    secret = TwoFAService.generate_secret()
    qr_uri = TwoFAService.get_provisioning_uri(secret, 'user@example.com', 'MyApp')
    qr_base64 = TwoFAService.generate_qr_code_base64(qr_uri)

    # Verify code from authenticator
    if TwoFAService.verify_code(secret, user_code):
        print('2FA code valid!')

    # Generate and hash backup codes
    codes = TwoFAService.generate_backup_codes()
    hashed = TwoFAService.hash_backup_codes(codes)

    # Exception logging decorator
    from v_flask.services import log_exceptions

    @app.route('/api/projekt/<int:id>', methods=['DELETE'])
    @log_exceptions('projekt')
    def delete_projekt(id):
        ...

    # Optional: Enable async logging
    from v_flask.services import init_async_logging, shutdown_async_logging
    init_async_logging()  # During app startup
    import atexit
    atexit.register(shutdown_async_logging)  # During shutdown
"""

from v_flask.services.logging_service import (
    log_event,
    log_niedrig,
    log_mittel,
    log_hoch,
    log_kritisch,
    log_exceptions,
    get_logs_for_entity,
    get_logs_for_user,
    init_async_logging,
    shutdown_async_logging,
)

from v_flask.services.email_service import (
    EmailResult,
    EmailServiceInterface,
    QuotaExceededError,
    NullEmailService,
)

from v_flask.services.brevo_service import (
    BrevoService,
    get_email_service,
    reset_email_service,
)

from v_flask.services.two_fa_service import (
    TwoFAService,
    log_2fa_event,
)

__all__ = [
    # Logging - Main function
    'log_event',
    # Logging - Convenience wrappers by importance
    'log_niedrig',
    'log_mittel',
    'log_hoch',
    'log_kritisch',
    # Logging - Exception decorator
    'log_exceptions',
    # Logging - Query helpers
    'get_logs_for_entity',
    'get_logs_for_user',
    # Logging - Async control
    'init_async_logging',
    'shutdown_async_logging',
    # Email - Result and Exceptions
    'EmailResult',
    'QuotaExceededError',
    # Email - Interfaces
    'EmailServiceInterface',
    'NullEmailService',
    # Email - Implementations
    'BrevoService',
    # Email - Factory
    'get_email_service',
    'reset_email_service',
    # Two-Factor Authentication
    'TwoFAService',
    'log_2fa_event',
]
