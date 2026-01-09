"""
v-flask Models

All SQLAlchemy models for the core system.

Usage:
    from v_flask.models import User, Rolle, Permission, Config, Betreiber, AuditLog
    from v_flask.models import LookupWert, Modul

    # Create a role with permissions
    admin = Rolle(name='admin', beschreibung='Administrator')
    perm = Permission(code='admin.*', beschreibung='Vollzugriff')
    admin.permissions.append(perm)

    # Create a user
    user = User(
        email='admin@example.com',
        vorname='Admin',
        nachname='User',
        rolle_id=admin.id
    )
    user.set_password('secret')

    # Check permissions
    if user.has_permission('user.delete'):
        print('User can delete users')

    # Get lookup values for a category
    statuses = LookupWert.get_for_kategorie('status', betreiber_id=1)

    # Get modules visible to user
    visible_modules = Modul.get_for_user(current_user)
"""

# Import order matters due to dependencies
from v_flask.models.permission import Permission, rolle_permission
from v_flask.models.rolle import Rolle
from v_flask.models.user import User, UserTyp
from v_flask.models.config import Config
from v_flask.models.betreiber import Betreiber
from v_flask.models.audit_log import AuditLog
from v_flask.models.lookup_wert import LookupWert
from v_flask.models.modul import Modul
from v_flask.models.plugin_activation import PluginActivation
from v_flask.models.system_status import SystemStatus

__all__ = [
    # Core user system
    'User',
    'UserTyp',
    'Rolle',
    'Permission',
    'rolle_permission',
    # Configuration
    'Config',
    'Betreiber',
    # Logging
    'AuditLog',
    # Dynamic values and modules
    'LookupWert',
    'Modul',
    # Plugin management
    'PluginActivation',
    'SystemStatus',
]
