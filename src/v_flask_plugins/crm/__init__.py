"""CRM (Customer Relationship Management) Plugin for v-flask.

A comprehensive B2B customer management plugin providing:
- Customer master data with VAT-ID validation
- Contact persons (Ansprechpartner)
- Billing and shipping addresses
- Customer groups for pricing tiers
- Shop authentication with bcrypt and brute-force protection

This is a core plugin that provides customer data for other plugins
like Shop, Pricing, and Invoicing.

Usage:
    from v_flask import VFlask
    from v_flask_plugins.crm import CRMPlugin

    v_flask = VFlask()
    v_flask.register_plugin(CRMPlugin())
    v_flask.init_app(app)

Dependencies:
    None (core plugin)
"""

from pathlib import Path

from v_flask.plugins import PluginManifest


class CRMPlugin(PluginManifest):
    """Customer Relationship Management plugin for v-flask applications.

    Provides:
        - Customer CRUD with VAT-ID validation
        - Contact person management
        - Billing/Shipping address management
        - Customer groups (for pricing integration)
        - Shop authentication (bcrypt, brute-force protection)
        - CSV import/export
    """

    name = 'crm'
    version = '0.1.0'
    description = 'Kundenverwaltung (CRM) für B2B-Geschäftskunden'
    author = 'v-flask'

    # No dependencies - this is a core plugin
    dependencies = []

    # Marketplace metadata
    long_description = '''
Ein umfassendes B2B-Kundenverwaltungs-Plugin für v-flask Anwendungen.

**Features:**
- Geschäftskunden mit Firmendaten und USt-IdNr.
- Ansprechpartner-Verwaltung (Haupt-AP, Abteilungen)
- Rechnungs- und Lieferadressen
- Kundengruppen für Preiskonditionen
- Shop-Authentifizierung mit Brute-Force-Schutz
- CSV-Import/Export

**Konsumenten:**
Dieses Plugin stellt Kundendaten für Shop-, Pricing- und Rechnungs-Plugins bereit.
'''
    license = 'MIT'
    categories = ['customers', 'admin', 'core']
    tags = ['crm', 'customers', 'b2b', 'contacts', 'addresses', 'authentication']
    min_v_flask_version = '0.2.0'

    # Admin navigation: appears under "Verwaltung" category
    admin_category = 'management'

    # UI Slots: Automatic UI integration when plugin is activated
    ui_slots = {
        'admin_menu': [
            {
                'label': 'Kunden',
                'url': 'crm_admin.list_customers',
                'icon': 'ti ti-users',
                'permission': 'admin.*',
                'order': 20,
            },
            # MVP: Kundengruppen-Menüeintrag hier hinzufügen
        ],
        'admin_dashboard_widgets': [
            {
                'name': 'Kundenverwaltung',
                'description': 'B2B-Kunden verwalten',
                'url': 'crm_admin.list_customers',
                'icon': 'ti-users',
                'color_hex': '#10b981',
            }
        ],
    }

    def get_models(self):
        """Return all CRM plugin models (Lazy Import!).

        Models are returned in dependency order:
        1. CustomerGroup (no dependencies)
        2. Customer (depends on CustomerGroup)
        3. Contact (depends on Customer)
        4. Address (depends on Customer)
        5. CustomerAuth (depends on Customer)
        """
        from v_flask_plugins.crm.models import (
            CustomerGroup,
            Customer,
            Contact,
            Address,
            CustomerAuth,
        )
        return [
            CustomerGroup,  # No FK dependencies, load first
            Customer,       # Depends on CustomerGroup
            Contact,        # Depends on Customer
            Address,        # Depends on Customer
            CustomerAuth,   # Depends on Customer
        ]

    def get_blueprints(self):
        """Return admin and API blueprints for CRM (Lazy Import!)."""
        from v_flask_plugins.crm.routes import crm_admin_bp, crm_api_bp
        return [
            (crm_admin_bp, '/admin/crm'),
            (crm_api_bp, ''),  # API routes have their own prefix
        ]

    def get_template_folder(self):
        """Return path to plugin templates."""
        return Path(__file__).parent / 'templates'

    def get_settings_schema(self) -> list[dict]:
        """Define available settings for the CRM plugin.

        Returns:
            List of setting definitions for CRM configuration.
        """
        return [
            {
                'key': 'customer_number_format',
                'label': 'Kundennummer-Format',
                'type': 'string',
                'description': 'Format für automatisch generierte Kundennummern (K-{YYYY}-{NNNNN})',
                'default': 'K-{YYYY}-{NNNNN}',
            },
            {
                'key': 'customer_number_start',
                'label': 'Kundennummer-Startwert',
                'type': 'int',
                'description': 'Startwert für die Nummerierung',
                'default': 1,
                'min': 1,
            },
            {
                'key': 'password_min_length',
                'label': 'Min. Passwortlänge',
                'type': 'int',
                'description': 'Minimale Passwortlänge für Shop-Login',
                'default': 8,
                'min': 6,
                'max': 32,
            },
            {
                'key': 'password_require_special',
                'label': 'Sonderzeichen erforderlich',
                'type': 'bool',
                'description': 'Passwort muss Sonderzeichen enthalten',
                'default': False,
            },
            {
                'key': 'password_reset_hours',
                'label': 'Reset-Token Gültigkeit (Std.)',
                'type': 'int',
                'description': 'Gültigkeit des Passwort-Reset-Tokens in Stunden',
                'default': 24,
                'min': 1,
                'max': 168,
            },
            {
                'key': 'brute_force_attempts',
                'label': 'Max. Login-Versuche',
                'type': 'int',
                'description': 'Anzahl fehlgeschlagener Logins vor Sperrung',
                'default': 5,
                'min': 3,
                'max': 20,
            },
            {
                'key': 'brute_force_lockout_minutes',
                'label': 'Sperrzeit (Min.)',
                'type': 'int',
                'description': 'Account-Sperrzeit nach zu vielen Fehlversuchen',
                'default': 15,
                'min': 5,
                'max': 1440,
            },
            {
                'key': 'default_country',
                'label': 'Standard-Land',
                'type': 'select',
                'description': 'Standard-Ländercode für neue Adressen',
                'options': [
                    {'value': 'DE', 'label': 'Deutschland'},
                    {'value': 'AT', 'label': 'Österreich'},
                    {'value': 'CH', 'label': 'Schweiz'},
                ],
                'default': 'DE',
            },
        ]

    def on_init(self, app):
        """Initialize CRM plugin services and context processors."""
        app.logger.info(f'CRM Plugin v{self.version} initialized')

        @app.context_processor
        def crm_context():
            """Provide CRM helper functions to templates."""

            def get_customer_count():
                """Get total active customer count for dashboard."""
                try:
                    from v_flask_plugins.crm.models import Customer
                    from v_flask.extensions import db
                    return db.session.query(Customer).filter_by(
                        status='active'
                    ).count()
                except Exception:
                    return 0

            return {
                'get_customer_count': get_customer_count,
            }


# Export the plugin class
__all__ = ['CRMPlugin']
