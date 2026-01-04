"""Tests for logging service."""

import pytest
from unittest.mock import patch, MagicMock

from flask import Flask
from flask_login import login_user

from v_flask import VFlask, db
from v_flask.models import AuditLog, User, Rolle
from v_flask.services import (
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
from v_flask.services.logging_service import _log_queue, _async_enabled


class TestLoggingService:
    """Test cases for logging service."""

    def test_log_event_basic(self, app):
        """Test basic log event creation."""
        with app.app_context():
            log_event('projekt', 'erstellt', 'Neues Projekt angelegt')

            log = db.session.query(AuditLog).first()
            assert log is not None
            assert log.modul == 'projekt'
            assert log.aktion == 'erstellt'
            assert log.details == 'Neues Projekt angelegt'
            assert log.wichtigkeit == 'niedrig'  # default

    def test_log_event_with_entity(self, app):
        """Test log event with entity reference."""
        with app.app_context():
            log_event(
                'projekt',
                'gelöscht',
                'Projekt wurde gelöscht',
                entity_type='Projekt',
                entity_id=42
            )

            log = db.session.query(AuditLog).first()
            assert log.entity_type == 'Projekt'
            assert log.entity_id == 42

    def test_log_niedrig(self, app):
        """Test log_niedrig convenience function."""
        with app.app_context():
            log_niedrig('user', 'angezeigt', 'Liste aufgerufen')

            log = db.session.query(AuditLog).first()
            assert log.wichtigkeit == 'niedrig'

    def test_log_mittel(self, app):
        """Test log_mittel convenience function."""
        with app.app_context():
            log_mittel('user', 'aktualisiert', 'Name geändert')

            log = db.session.query(AuditLog).first()
            assert log.wichtigkeit == 'mittel'

    def test_log_hoch(self, app):
        """Test log_hoch convenience function."""
        with app.app_context():
            log_hoch('user', 'gelöscht', 'User entfernt')

            log = db.session.query(AuditLog).first()
            assert log.wichtigkeit == 'hoch'

    def test_log_kritisch(self, app):
        """Test log_kritisch convenience function."""
        with app.app_context():
            log_kritisch('auth', 'login_failed', 'Falsches Passwort')

            log = db.session.query(AuditLog).first()
            assert log.wichtigkeit == 'kritisch'

    def test_log_with_authenticated_user(self, app, admin_user):
        """Test that user_id is captured when user is logged in."""
        with app.app_context():
            with app.test_request_context():
                # Simulate logged in user
                user = db.session.get(User, admin_user.id)
                login_user(user)

                log_event('test', 'action', 'Test action')

                log = db.session.query(AuditLog).first()
                assert log.user_id == user.id

    def test_log_with_ip_address(self, app):
        """Test that IP address is captured from request."""
        with app.app_context():
            with app.test_request_context(environ_base={'REMOTE_ADDR': '192.168.1.100'}):
                log_event('test', 'action', 'Test')

                log = db.session.query(AuditLog).first()
                assert log.ip_address == '192.168.1.100'

    def test_log_with_x_forwarded_for(self, app):
        """Test that X-Forwarded-For header is respected."""
        with app.app_context():
            with app.test_request_context(headers={'X-Forwarded-For': '10.0.0.1, 192.168.1.1'}):
                log_event('test', 'action', 'Test')

                log = db.session.query(AuditLog).first()
                assert log.ip_address == '10.0.0.1'  # First IP in chain

    def test_get_logs_for_entity(self, app):
        """Test getting logs for a specific entity."""
        with app.app_context():
            # Create multiple logs for different entities
            log_event('projekt', 'a', entity_type='Projekt', entity_id=1)
            log_event('projekt', 'b', entity_type='Projekt', entity_id=1)
            log_event('projekt', 'c', entity_type='Projekt', entity_id=2)
            log_event('task', 'd', entity_type='Task', entity_id=1)

            logs = get_logs_for_entity('Projekt', 1)
            assert len(logs) == 2
            assert all(l.entity_type == 'Projekt' and l.entity_id == 1 for l in logs)

    def test_get_logs_for_entity_limit(self, app):
        """Test log limit for entity queries."""
        with app.app_context():
            for i in range(10):
                log_event('test', f'action_{i}', entity_type='Test', entity_id=1)

            logs = get_logs_for_entity('Test', 1, limit=5)
            assert len(logs) == 5

    def test_get_logs_for_user(self, app, admin_user):
        """Test getting logs created by a specific user."""
        with app.app_context():
            user = db.session.get(User, admin_user.id)

            # Create logs with user context
            with app.test_request_context():
                login_user(user)
                log_event('test', 'user_action_1')
                log_event('test', 'user_action_2')

            logs = get_logs_for_user(user.id)
            assert len(logs) == 2
            assert all(l.user_id == user.id for l in logs)
            assert all(l.aktion.startswith('user_action') for l in logs)


class TestLogExceptionsDecorator:
    """Test cases for log_exceptions decorator."""

    def test_decorator_logs_exception(self, app):
        """Test that exceptions are logged."""
        with app.app_context():
            @log_exceptions('test_modul')
            def failing_function():
                raise ValueError('Test error')

            with pytest.raises(ValueError):
                failing_function()

            log = db.session.query(AuditLog).first()
            assert log.modul == 'test_modul'
            assert log.aktion == 'exception'
            assert 'ValueError: Test error' in log.details
            assert log.wichtigkeit == 'kritisch'

    def test_decorator_reraises_exception(self, app):
        """Test that exceptions are re-raised after logging."""
        with app.app_context():
            @log_exceptions('test')
            def failing_function():
                raise RuntimeError('Must be raised')

            with pytest.raises(RuntimeError, match='Must be raised'):
                failing_function()

    def test_decorator_passes_on_success(self, app):
        """Test that successful functions work normally."""
        with app.app_context():
            @log_exceptions('test')
            def successful_function(x, y):
                return x + y

            result = successful_function(2, 3)
            assert result == 5

            # No log should be created
            logs = db.session.query(AuditLog).all()
            assert len(logs) == 0


class TestAsyncLogging:
    """Test cases for async logging functionality."""

    def test_init_and_shutdown(self, app):
        """Test initializing and shutting down async logging."""
        with app.app_context():
            # Initialize
            init_async_logging()

            from v_flask.services.logging_service import _async_enabled, _log_queue
            assert _async_enabled is True
            assert _log_queue is not None

            # Shutdown
            shutdown_async_logging()

            from v_flask.services.logging_service import _async_enabled as enabled_after
            assert enabled_after is False

    def test_double_init_is_safe(self, app):
        """Test that calling init_async_logging twice is safe."""
        with app.app_context():
            init_async_logging()
            init_async_logging()  # Should not raise

            shutdown_async_logging()
