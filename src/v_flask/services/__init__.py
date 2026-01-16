"""
v-flask Services

Logging, Email und andere Dienste.

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
]
