"""CRM Plugin Routes.

Admin routes for customer management.
API routes for shop integration (POC: login only).
"""

from v_flask_plugins.crm.routes.admin import crm_admin_bp
from v_flask_plugins.crm.routes.api import crm_api_bp

__all__ = ['crm_admin_bp', 'crm_api_bp']
