"""Restart manager service for handling server restarts."""

from __future__ import annotations

import logging
import os
import signal
import sys
from datetime import datetime, UTC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask

logger = logging.getLogger(__name__)


class RestartError(Exception):
    """Base exception for restart errors."""

    pass


class RestartManager:
    """Handles server restart scheduling and execution.

    The RestartManager provides:
    - Request immediate restart
    - Schedule restart for a specific time
    - Cancel scheduled restarts
    - Execute the actual restart (via SIGHUP or process restart)

    Note: Scheduled restarts require an external scheduler or cron job
    to poll the scheduled time and execute the restart.

    Usage:
        restart_manager = RestartManager()

        # Request immediate restart
        restart_manager.request_restart(immediate=True)

        # Schedule restart
        from datetime import datetime, timedelta
        restart_manager.schedule_restart(datetime.now() + timedelta(hours=2))

        # Check scheduled restart
        scheduled = restart_manager.get_scheduled_restart()
        if scheduled:
            print(f"Restart scheduled for {scheduled}")

        # Execute restart (usually called by scheduler)
        restart_manager.execute_restart()
    """

    def __init__(self, app: Flask | None = None):
        """Initialize the restart manager.

        Args:
            app: Optional Flask app for configuration.
        """
        self.app = app

    def request_restart(self, immediate: bool = False) -> None:
        """Request a server restart.

        If immediate=True, attempts to restart right away.
        Otherwise just sets the restart_required flag.

        Args:
            immediate: If True, restart immediately.
        """
        from v_flask.models import SystemStatus

        SystemStatus.set_bool(SystemStatus.KEY_RESTART_REQUIRED, True)

        if immediate:
            self.execute_restart()

    def schedule_restart(self, at: datetime) -> None:
        """Schedule a restart for a specific time.

        Note: The actual execution of scheduled restarts requires
        an external scheduler (cron, celery, apscheduler) to check
        for scheduled restarts and execute them.

        Args:
            at: DateTime when the restart should occur.
        """
        from v_flask.models import SystemStatus

        SystemStatus.set_datetime(SystemStatus.KEY_RESTART_SCHEDULED, at)
        SystemStatus.set_bool(SystemStatus.KEY_RESTART_REQUIRED, True)

        logger.info(f"Restart scheduled for {at.isoformat()}")

    def cancel_scheduled_restart(self) -> None:
        """Cancel a scheduled restart."""
        from v_flask.models import SystemStatus

        SystemStatus.delete(SystemStatus.KEY_RESTART_SCHEDULED)
        logger.info("Scheduled restart cancelled")

    def get_scheduled_restart(self) -> datetime | None:
        """Get scheduled restart time, if any.

        Returns:
            DateTime of scheduled restart or None.
        """
        from v_flask.models import SystemStatus
        return SystemStatus.get_datetime(SystemStatus.KEY_RESTART_SCHEDULED)

    def is_restart_due(self) -> bool:
        """Check if a scheduled restart is due.

        Returns:
            True if a restart is scheduled and the time has passed.
        """
        scheduled = self.get_scheduled_restart()
        if not scheduled:
            return False

        return datetime.now(UTC) >= scheduled

    def execute_restart(self) -> None:
        """Execute the actual server restart.

        This method attempts to restart the server using various methods
        depending on the deployment environment:

        1. Development (flask run with reloader): Touch a watched file
        2. Gunicorn: Send SIGHUP to master process
        3. Other: Send SIGHUP to current process

        Raises:
            RestartError: If restart could not be executed.
        """
        from v_flask.models import SystemStatus

        logger.info("Executing server restart...")

        # Clear the scheduled restart
        SystemStatus.delete(SystemStatus.KEY_RESTART_SCHEDULED)

        # Try different restart methods based on environment
        if self._is_development():
            self._restart_development()
        elif self._is_gunicorn():
            self._restart_gunicorn()
        else:
            self._restart_generic()

    def _is_development(self) -> bool:
        """Check if running in development mode with Flask reloader."""
        return os.environ.get('FLASK_ENV') == 'development' or \
               os.environ.get('FLASK_DEBUG') == '1' or \
               'WERKZEUG_RUN_MAIN' in os.environ

    def _is_gunicorn(self) -> bool:
        """Check if running under gunicorn."""
        return 'gunicorn' in sys.modules

    def _restart_development(self) -> None:
        """Restart in development mode.

        In development with Flask reloader, we can trigger a restart by:
        1. Sending SIGHUP to the process
        2. Or by touching a watched Python file
        """
        try:
            # Send SIGHUP to trigger reload
            os.kill(os.getpid(), signal.SIGHUP)
            logger.info("Sent SIGHUP for development restart")
        except Exception as e:
            logger.warning(f"SIGHUP failed, trying alternate method: {e}")
            # Alternative: touch a Python file to trigger reloader
            self._touch_for_reload()

    def _restart_gunicorn(self) -> None:
        """Restart gunicorn by sending SIGHUP to master.

        Gunicorn handles SIGHUP by gracefully restarting workers.
        """
        try:
            # Get the master process PID
            master_pid = os.getppid()
            os.kill(master_pid, signal.SIGHUP)
            logger.info(f"Sent SIGHUP to gunicorn master (PID {master_pid})")
        except Exception as e:
            raise RestartError(f"Failed to restart gunicorn: {e}")

    def _restart_generic(self) -> None:
        """Generic restart by sending SIGHUP to current process."""
        try:
            os.kill(os.getpid(), signal.SIGHUP)
            logger.info("Sent SIGHUP for generic restart")
        except Exception as e:
            raise RestartError(f"Failed to send restart signal: {e}")

    def _touch_for_reload(self) -> None:
        """Touch the main module file to trigger Flask reloader."""
        try:
            # Try to touch the main application file
            import v_flask
            module_file = v_flask.__file__
            if module_file:
                os.utime(module_file, None)
                logger.info(f"Touched {module_file} for reload")
        except Exception as e:
            logger.warning(f"Could not touch file for reload: {e}")

    def clear_restart_flag(self) -> None:
        """Clear the restart_required flag after restart.

        Call this during app startup to indicate restart is complete.
        """
        from v_flask.models import SystemStatus
        SystemStatus.set_bool(SystemStatus.KEY_RESTART_REQUIRED, False)

    def check_and_execute_scheduled(self) -> bool:
        """Check for scheduled restarts and execute if due.

        This method should be called periodically (e.g., every minute)
        by an external scheduler to handle scheduled restarts.

        Returns:
            True if a restart was executed.
        """
        if self.is_restart_due():
            self.execute_restart()
            return True
        return False
