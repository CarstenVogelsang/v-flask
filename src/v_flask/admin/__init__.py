"""Core admin module for v-flask framework.

Provides the base admin blueprint with dashboard route that all
core admin templates depend on.
"""

from v_flask.admin.routes import admin_bp, register_admin_routes

__all__ = ['admin_bp', 'register_admin_routes']
