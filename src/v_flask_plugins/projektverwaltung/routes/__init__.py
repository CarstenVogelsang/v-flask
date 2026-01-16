"""Routes for Projektverwaltung plugin.

This module exports the admin and API blueprints.
"""
from v_flask_plugins.projektverwaltung.routes.admin import admin_bp
from v_flask_plugins.projektverwaltung.routes.api import api_bp

__all__ = ['admin_bp', 'api_bp']
