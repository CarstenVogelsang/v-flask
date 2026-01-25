"""Pricing Plugin for v-flask.

A bridge plugin connecting PIM (products) and CRM (customers)
for customer-specific price calculation.

POC Scope:
- Customer-specific product prices only
- Fixed price or percentage discount
- No tier pricing
- No time-limited rules

Usage:
    from v_flask import VFlask
    from v_flask_plugins.pricing import PricingPlugin

    v_flask = VFlask()
    v_flask.register_plugin(PricingPlugin())
    v_flask.init_app(app)

Dependencies:
    - pim: Required for product data
    - crm: Required for customer data
"""

from pathlib import Path

from v_flask.plugins import PluginManifest


class PricingPlugin(PluginManifest):
    """Pricing plugin for customer-specific prices."""

    name = 'pricing'
    version = '0.1.0'
    description = 'Kundenspezifische Preise und Rabatte'
    author = 'v-flask'

    # Required dependencies
    dependencies = ['pim', 'crm']

    # Marketplace metadata
    long_description = '''
Kundenspezifische Preisfindung für B2B-Shops.

**POC-Features:**
- Kundenspezifische Artikelpreise (Festpreis oder Rabatt)
- Admin-UI zur Regelverwaltung
- API für Shop-Integration

**MVP (geplant):**
- Rabatte auf Marke, Serie, Hersteller, Warengruppe
- Staffelpreise
- Zeitlich begrenzte Konditionen
- Mindestmarge-Warnung
'''
    license = 'MIT'
    categories = ['pricing', 'admin', 'bridge']
    tags = ['pricing', 'discounts', 'b2b', 'customers']
    min_v_flask_version = '0.2.0'

    admin_category = 'management'

    ui_slots = {
        'admin_menu': [
            # POC: Access via customer detail, not main menu
        ],
        'admin_dashboard_widgets': [
            {
                'name': 'Preiskonditionen',
                'description': 'Kundenspezifische Preise verwalten',
                'url': 'crm_admin.list_customers',  # Navigate via CRM
                'icon': 'ti-currency-euro',
                'color_hex': '#f59e0b',
            }
        ],
    }

    def get_models(self):
        """Return all Pricing plugin models (Lazy Import!)."""
        from v_flask_plugins.pricing.models import PricingRule
        return [PricingRule]

    def get_blueprints(self):
        """Return admin and API blueprints (Lazy Import!)."""
        from v_flask_plugins.pricing.routes import pricing_admin_bp, pricing_api_bp
        return [
            (pricing_admin_bp, '/admin/pricing'),
            (pricing_api_bp, ''),  # API at root level
        ]

    def get_template_folder(self):
        """Return path to plugin templates."""
        return Path(__file__).parent / 'templates'

    def on_init(self, app):
        """Initialize Pricing plugin."""
        app.logger.info(f'Pricing Plugin v{self.version} initialized (POC)')


# Export the plugin class
__all__ = ['PricingPlugin']
