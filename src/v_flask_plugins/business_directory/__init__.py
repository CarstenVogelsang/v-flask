"""Business Directory Plugin.

Ein Multi-Directory Plugin für Business-Verzeichnisse mit:
- Mehrere Verzeichnistypen pro Projekt (z.B. Händler + Hersteller)
- Konfigurierbares Field-Schema pro Verzeichnistyp
- Geo-Hierarchie (Land → Bundesland → Kreis → Ort)
- Self-Registration Wizard
- Ownership Claiming
"""

from pathlib import Path

from v_flask.plugins import PluginManifest


class BusinessDirectoryPlugin(PluginManifest):
    """Plugin für Multi-Directory Business-Verzeichnisse."""

    # Pflicht-Metadaten
    name = 'business_directory'
    version = '0.1.0'
    description = 'Multi-Directory Business-Verzeichnis mit Self-Registration'
    author = 'v-flask'

    # Marketplace-Metadaten
    license = 'MIT'
    categories = ['directory', 'business']
    tags = ['verzeichnis', 'business', 'geo', 'registration']
    min_v_flask_version = '1.0.0'

    # Optional: Abhängigkeiten
    dependencies = []  # Keine Plugin-Abhängigkeiten

    # Admin-Navigation Kategorie
    admin_category = 'directory'

    # UI-Slots für automatische Integration
    ui_slots = {
        'admin_menu': [
            {
                'label': 'Verzeichnistypen',
                'url': 'business_directory_admin_types.list_types',
                'icon': 'ti ti-list-details',
                'permission': 'admin.*',
                'order': 10,
            },
            {
                'label': 'Einträge',
                'url': 'business_directory_admin.list_entries',
                'icon': 'ti ti-building-store',
                'permission': 'business_directory.read',
                'order': 11,
            },
            {
                'label': 'Geodaten',
                'url': 'business_directory_admin_geodaten.index',
                'icon': 'ti ti-map-2',
                'permission': 'admin.*',
                'order': 12,
            },
            {
                'label': 'Review Queue',
                'url': 'business_directory_admin.review_queue',
                'icon': 'ti ti-clipboard-check',
                'permission': 'business_directory.review',
                'order': 13,
            },
        ],
        'admin_dashboard_widgets': [
            {
                'name': 'Verzeichnis',
                'description': 'Business-Verzeichnis verwalten',
                'url': 'business_directory_admin.entries_list',
                'icon': 'ti-building-store',
                'color_hex': '#3b82f6',
            },
        ],
    }

    def get_models(self):
        """SQLAlchemy Models zurückgeben (Lazy Import!)."""
        from .models import (
            DirectoryType,
            DirectoryEntry,
            RegistrationDraft,
            ClaimRequest,
            GeoLand,
            GeoBundesland,
            GeoKreis,
            GeoOrt,
        )
        return [
            DirectoryType,
            DirectoryEntry,
            RegistrationDraft,
            ClaimRequest,
            GeoLand,
            GeoBundesland,
            GeoKreis,
            GeoOrt,
        ]

    def get_blueprints(self):
        """Blueprints mit URL-Prefix zurückgeben (Lazy Import!)."""
        from .routes import (
            public_bp,
            admin_bp,
            admin_types_bp,
            admin_geodaten_bp,
            register_bp,
            provider_bp,
            api_bp,
        )
        return [
            (public_bp, ''),  # Root-Level für Geo-Drilling
            (admin_bp, '/admin/directory'),
            (admin_types_bp, '/admin/directory/types'),
            (admin_geodaten_bp, '/admin/directory/geodaten'),
            (register_bp, '/register'),
            (provider_bp, '/provider'),
            (api_bp, '/api/directory'),
        ]

    def get_template_folder(self):
        """Template-Verzeichnis zurückgeben."""
        return Path(__file__).parent / 'templates'

    def get_cli_commands(self):
        """CLI-Befehle zurückgeben."""
        from .cli import directory_cli
        return [directory_cli]

    def get_settings_schema(self):
        """Konfigurierbare Plugin-Einstellungen."""
        return [
            {
                'key': 'unternehmensdaten_api_key',
                'label': 'Unternehmensdaten.org API Key',
                'type': 'password',
                'description': 'API Key für Geodaten-Import (Deutschland)',
                'required': False,
            },
            {
                'key': 'geoapify_api_key',
                'label': 'Geoapify API Key',
                'type': 'password',
                'description': 'API Key für Business-Suche (optional)',
                'required': False,
            },
            {
                'key': 'enable_self_registration',
                'label': 'Self-Registration aktivieren',
                'type': 'bool',
                'description': 'Erlaubt Anbietern, sich selbst zu registrieren',
                'default': True,
            },
            {
                'key': 'enable_claiming',
                'label': 'Claiming aktivieren',
                'type': 'bool',
                'description': 'Erlaubt Anbietern, bestehende Einträge zu beanspruchen',
                'default': True,
            },
            {
                'key': 'require_verification',
                'label': 'Verifizierung erforderlich',
                'type': 'bool',
                'description': 'Neue Einträge müssen von Admin freigegeben werden',
                'default': True,
            },
        ]

    def on_init(self, app):
        """Wird beim App-Start aufgerufen."""
        app.logger.info(f'Plugin {self.name} v{self.version} initialisiert')
        app.logger.debug(
            f'Business Directory: Self-Registration und Geo-Hierarchie verfügbar'
        )


# Export für einfachen Import
__all__ = ['BusinessDirectoryPlugin']
