"""Core admin routes for v-flask framework.

Provides the base admin blueprint with dashboard that all
core admin templates depend on. This blueprint is automatically
registered by VFlask and provides:

- /admin/ - Dashboard (redirects to plugins list)

All satellite projects using v-flask automatically get these
routes without any additional configuration.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from flask import Blueprint, redirect, url_for

from v_flask.auth import admin_required

if TYPE_CHECKING:
    from flask import Flask

logger = logging.getLogger(__name__)

# Core admin blueprint
admin_bp = Blueprint(
    'admin',
    __name__,
    url_prefix='/admin',
    template_folder='../templates',
)


@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard - redirects to first available admin page.

    The dashboard serves as the entry point to the admin area.
    Currently redirects to the plugins management page.
    """
    return redirect(url_for('plugins_admin.list_plugins'))


def register_admin_routes(app: Flask) -> None:
    """Register the core admin blueprint with the app.

    Args:
        app: Flask application instance.
    """
    app.register_blueprint(admin_bp)
    logger.info("Registered core admin routes at /admin/")
