"""Logging service for audit trail and event tracking."""

from __future__ import annotations

import threading
from functools import wraps
from queue import Queue
from typing import TYPE_CHECKING, Callable

from flask import current_app, has_request_context, request
from flask_login import current_user

from v_flask.extensions import db

if TYPE_CHECKING:
    from v_flask.models import AuditLog


# Async logging queue and worker
_log_queue: Queue | None = None
_worker_thread: threading.Thread | None = None
_async_enabled: bool = False


def _get_current_user_id() -> int | None:
    """Get the current user's ID if available."""
    try:
        if current_user and current_user.is_authenticated:
            return current_user.id
    except RuntimeError:
        # Outside of request context
        pass
    return None


def _get_client_ip() -> str | None:
    """Get the client's IP address if in request context."""
    if has_request_context():
        # Handle proxies (X-Forwarded-For)
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        return request.remote_addr
    return None


def _do_log(
    modul: str,
    aktion: str,
    details: str | None = None,
    wichtigkeit: str = 'niedrig',
    entity_type: str | None = None,
    entity_id: int | None = None,
    user_id: int | None = None,
    ip_address: str | None = None
) -> None:
    """Internal function to create the AuditLog entry."""
    from v_flask.models import AuditLog

    log_entry = AuditLog(
        user_id=user_id,
        modul=modul,
        aktion=aktion,
        details=details,
        wichtigkeit=wichtigkeit,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address
    )
    db.session.add(log_entry)
    db.session.commit()


def _async_worker():
    """Background worker for async logging."""
    while True:
        item = _log_queue.get()
        if item is None:  # Shutdown signal
            _log_queue.task_done()
            break
        try:
            _do_log(**item)
        except Exception as e:
            # Log errors to stderr, don't crash the worker
            import sys
            print(f"Async logging error: {e}", file=sys.stderr)
        finally:
            _log_queue.task_done()


def init_async_logging():
    """Initialize async logging with a background worker.

    Call this during app initialization if you want async logging:

        from v_flask.services import init_async_logging

        def create_app():
            app = Flask(__name__)
            v_flask = VFlask(app)
            init_async_logging()
            return app
    """
    global _log_queue, _worker_thread, _async_enabled

    if _async_enabled:
        return  # Already initialized

    _log_queue = Queue()
    _worker_thread = threading.Thread(target=_async_worker, daemon=True)
    _worker_thread.start()
    _async_enabled = True


def shutdown_async_logging():
    """Shutdown async logging worker gracefully.

    Call this during app teardown:

        import atexit
        atexit.register(shutdown_async_logging)
    """
    global _log_queue, _async_enabled

    if _log_queue and _async_enabled:
        _log_queue.put(None)  # Shutdown signal
        _log_queue.join()
        _async_enabled = False


def log_event(
    modul: str,
    aktion: str,
    details: str | None = None,
    wichtigkeit: str = 'niedrig',
    entity_type: str | None = None,
    entity_id: int | None = None
) -> None:
    """Log an audit event.

    Args:
        modul: Module name (e.g., 'projekt', 'user', 'auth').
        aktion: Action performed (e.g., 'erstellt', 'gelöscht', 'login').
        details: Additional details about the event.
        wichtigkeit: Importance level ('niedrig', 'mittel', 'hoch', 'kritisch').
        entity_type: Type of entity affected (e.g., 'Projekt', 'User').
        entity_id: ID of the affected entity.

    Usage:
        from v_flask.services import log_event

        # Log a simple event
        log_event('projekt', 'erstellt', 'Projekt "Website Relaunch" erstellt')

        # Log with entity reference
        log_event(
            modul='projekt',
            aktion='gelöscht',
            details='Projekt wurde gelöscht',
            wichtigkeit='hoch',
            entity_type='Projekt',
            entity_id=42
        )
    """
    log_data = {
        'modul': modul,
        'aktion': aktion,
        'details': details,
        'wichtigkeit': wichtigkeit,
        'entity_type': entity_type,
        'entity_id': entity_id,
        'user_id': _get_current_user_id(),
        'ip_address': _get_client_ip()
    }

    if _async_enabled and _log_queue:
        _log_queue.put(log_data)
    else:
        _do_log(**log_data)


def log_niedrig(modul: str, aktion: str, details: str | None = None, **kwargs) -> None:
    """Log a low-importance event (routine actions).

    Use for: View actions, list queries, read operations.
    """
    log_event(modul, aktion, details, wichtigkeit='niedrig', **kwargs)


def log_mittel(modul: str, aktion: str, details: str | None = None, **kwargs) -> None:
    """Log a medium-importance event (standard changes).

    Use for: Create, update operations, form submissions.
    """
    log_event(modul, aktion, details, wichtigkeit='mittel', **kwargs)


def log_hoch(modul: str, aktion: str, details: str | None = None, **kwargs) -> None:
    """Log a high-importance event (significant changes).

    Use for: Delete operations, bulk changes, permission changes.
    """
    log_event(modul, aktion, details, wichtigkeit='hoch', **kwargs)


def log_kritisch(modul: str, aktion: str, details: str | None = None, **kwargs) -> None:
    """Log a critical event (security-relevant).

    Use for: Login failures, permission denied, security events, exceptions.
    """
    log_event(modul, aktion, details, wichtigkeit='kritisch', **kwargs)


def log_exceptions(modul: str) -> Callable:
    """Decorator to automatically log exceptions in routes.

    Args:
        modul: Module name for the log entry.

    Usage:
        from v_flask.services import log_exceptions

        @app.route('/api/projekt/<int:id>', methods=['DELETE'])
        @log_exceptions('projekt')
        def delete_projekt(id):
            projekt = Projekt.query.get_or_404(id)
            db.session.delete(projekt)
            db.session.commit()
            return jsonify({'status': 'deleted'})

    If an exception occurs, it will be logged as kritisch and re-raised.
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                # Log the exception
                log_kritisch(
                    modul=modul,
                    aktion='exception',
                    details=f'{type(e).__name__}: {str(e)}'
                )
                # Re-raise the exception
                raise
        return wrapper
    return decorator


def get_logs_for_entity(
    entity_type: str,
    entity_id: int,
    limit: int = 50
) -> list:
    """Get audit logs for a specific entity.

    Args:
        entity_type: Type of entity (e.g., 'Projekt').
        entity_id: ID of the entity.
        limit: Maximum number of logs to return.

    Returns:
        List of AuditLog instances, newest first.
    """
    from v_flask.models import AuditLog

    return db.session.query(AuditLog).filter_by(
        entity_type=entity_type,
        entity_id=entity_id
    ).order_by(AuditLog.timestamp.desc()).limit(limit).all()


def get_logs_for_user(user_id: int, limit: int = 50) -> list:
    """Get audit logs created by a specific user.

    Args:
        user_id: User ID.
        limit: Maximum number of logs to return.

    Returns:
        List of AuditLog instances, newest first.
    """
    from v_flask.models import AuditLog

    return db.session.query(AuditLog).filter_by(
        user_id=user_id
    ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
