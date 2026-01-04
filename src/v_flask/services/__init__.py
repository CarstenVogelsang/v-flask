"""
v-flask Services

Logging und andere Dienste.

Usage:
    from v_flask.services import log_event, log_hoch, log_mittel, log_kritisch

    # Log a simple event
    log_event('projekt', 'erstellt', 'Projekt "Website" erstellt')

    # Log with importance level
    log_hoch('projekt', 'gelöscht', 'Projekt wurde gelöscht')

    # Use exception decorator
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

__all__ = [
    # Main logging function
    'log_event',
    # Convenience wrappers by importance
    'log_niedrig',
    'log_mittel',
    'log_hoch',
    'log_kritisch',
    # Exception decorator
    'log_exceptions',
    # Query helpers
    'get_logs_for_entity',
    'get_logs_for_user',
    # Async logging control
    'init_async_logging',
    'shutdown_async_logging',
]
