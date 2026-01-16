"""CRM UDO Plugin - Customer Relationship Management for UDO.

This plugin provides a UI for managing companies (Unternehmen),
organisations, and contacts via the UDO API.

It does NOT have local models - all data is fetched from the UDO API.
"""
from pathlib import Path
from v_flask.plugins import PluginManifest


class CrmUdoPlugin(PluginManifest):
    """CRM Plugin for UDO - manages companies, organisations, and contacts."""

    # Required metadata
    name = 'crm_udo'
    version = '1.0.0'
    description = 'CRM für Unternehmen, Organisationen und Kontakte (via UDO API)'
    author = 'v-flask'

    # Marketplace metadata
    license = 'MIT'
    categories = ['crm', 'admin']
    tags = ['crm', 'unternehmen', 'kontakte', 'udo']
    min_v_flask_version = '1.0.0'

    # No dependencies - relies on host app providing UDO_API_BASE_URL
    dependencies = []

    # Admin navigation category
    admin_category = 'data'

    # UI Slots for automatic integration
    ui_slots = {
        'admin_menu': [
            {
                'label': 'CRM',
                'url': 'crm_udo_admin.index',
                'icon': 'ti ti-building-community',
                'permission': 'admin.*',
                'order': 20,
            }
        ],
        'admin_dashboard_widgets': [
            {
                'name': 'CRM',
                'description': 'Unternehmen & Kontakte verwalten',
                'url': 'crm_udo_admin.index',
                'icon': 'ti-building-community',
                'color_hex': '#0ea5e9',
            }
        ],
    }

    def get_models(self):
        """No local models - all data via UDO API."""
        return []

    def get_blueprints(self):
        """Return admin blueprint (no public routes)."""
        from .routes.admin import admin_bp
        return [
            (admin_bp, '/admin/crm_udo'),
        ]

    def get_template_folder(self):
        """Return template directory path."""
        return Path(__file__).parent / 'templates'

    def on_init(self, app):
        """Called during app initialization."""
        # Verify UDO_API_BASE_URL is configured
        if not app.config.get('UDO_API_BASE_URL'):
            app.logger.warning(
                f'Plugin {self.name}: UDO_API_BASE_URL not configured. '
                'CRM functionality will not work.'
            )
        else:
            app.logger.info(f'Plugin {self.name} v{self.version} initialized')
