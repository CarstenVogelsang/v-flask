"""Routes for the Katalog plugin."""

from v_flask_plugins.katalog.routes.public import katalog_bp
from v_flask_plugins.katalog.routes.admin import katalog_admin_bp

__all__ = ['katalog_bp', 'katalog_admin_bp']
