"""API Market Plugin for v-flask.

A plugin for API marketplace functionality:
- Automatic documentation from OpenAPI specs
- API key management (via external API)
- Usage tracking and billing overview
- Code examples in Python, C#, Delphi

Usage:
    from v_flask import VFlask
    from v_flask_plugins.api_market import ApiMarketPlugin

    v_flask = VFlask()
    v_flask.register_plugin(ApiMarketPlugin())
    v_flask.init_app(app)
"""

from pathlib import Path

from v_flask.plugins import PluginManifest


class ApiMarketPlugin(PluginManifest):
    """API Marketplace plugin for v-flask applications.

    Provides:
        - Public API documentation at /api-market
        - Admin interface at /admin/api-market
        - OpenAPI spec fetching and documentation generation
        - Code example generation (Python, C#, Delphi)
    """

    name = 'api_market'
    version = '0.1.0'
    description = 'API-Marketplace mit automatischer Dokumentation aus OpenAPI-Specs'
    author = 'v-flask'

    # No dependencies on other plugins
    dependencies = []

    # Marketplace metadata
    long_description = '''
Ein API-Marketplace Plugin für v-flask Anwendungen.

**Features:**
- Automatische Dokumentation aus OpenAPI-Specs (live abgerufen)
- API-Key Management für Partner/Kunden
- Usage-Tracking und Abrechnungsübersicht
- Code-Beispiele in Python, C#, Delphi (auto-generiert)

Das Plugin ruft OpenAPI-Specs von externen APIs ab und generiert
daraus benutzerfreundliche Dokumentation mit Code-Beispielen.
'''
    license = 'MIT'
    categories = ['api', 'documentation', 'developer-tools']
    tags = ['api', 'marketplace', 'openapi', 'swagger', 'documentation', 'code-examples']
    min_v_flask_version = '0.2.0'

    # Admin navigation: appears under "Developer" category
    admin_category = 'system'

    # UI Slots: Automatic UI integration when plugin is activated
    ui_slots = {
        'navbar_items': [
            {
                'label': 'API',
                'url': 'api_market.list_apis',
                'icon': 'ti ti-api',
                'order': 50,
            }
        ],
        'admin_menu': [
            {
                'label': 'API Marketplace',
                'url': 'api_market_admin.dashboard',
                'icon': 'ti ti-api',
                'permission': 'admin.*',
                'order': 50,
            }
        ],
        'admin_dashboard_widgets': [
            {
                'name': 'APIs',
                'description': 'Registrierte APIs verwalten',
                'icon': 'ti-api',
                'url': 'api_market_admin.dashboard',
                'badge_func': 'get_api_count',
                'color_hex': '#6366f1',
                'order': 200,
            }
        ],
    }

    def get_api_count(self) -> int:
        """Get count of registered APIs.

        Used by ui_slots badge_func to display count in admin UI.
        """
        try:
            from v_flask.extensions import db
            from v_flask_plugins.api_market.models import ExternalApi
            return db.session.query(ExternalApi).filter_by(status='active').count()
        except Exception:
            return 0

    def get_models(self):
        """Return the ExternalApi model."""
        from v_flask_plugins.api_market.models import ExternalApi
        return [ExternalApi]

    def get_blueprints(self):
        """Return public and admin blueprints."""
        from v_flask_plugins.api_market.routes import api_market_bp, api_market_admin_bp
        return [
            (api_market_bp, '/api-market'),
            (api_market_admin_bp, '/admin/api-market'),
        ]

    def get_template_folder(self):
        """Return path to plugin templates."""
        return Path(__file__).parent / 'templates'

    def get_static_folder(self):
        """Return path to plugin static files."""
        return Path(__file__).parent / 'static'

    def on_init(self, app):
        """Initialize plugin with Flask app."""
        # Register configuration defaults
        app.config.setdefault('API_MARKET_CACHE_TTL', 3600)  # 1 hour
        app.config.setdefault('API_MARKET_CODE_LANGUAGES', ['python', 'csharp', 'delphi'])


# Export the plugin class
__all__ = ['ApiMarketPlugin']
