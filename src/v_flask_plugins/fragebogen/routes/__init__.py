"""Fragebogen Plugin Routes."""

from v_flask_plugins.fragebogen.routes.admin import admin_bp
from v_flask_plugins.fragebogen.routes.public import public_bp

__all__ = ['admin_bp', 'public_bp']
