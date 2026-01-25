"""Katalog Plugin - PDF-Blätterkatalog für v-flask.

Stellt PDF-Kataloge als Blätterkataloge im Browser dar und bietet
Download-Funktionalität. Ideal für Hersteller-Portale mit Produktkatalogen.

Features:
- PDF-Viewer im Browser (PDF.js)
- Kategorisierte Katalog-Verwaltung
- Download-Counter und View-Counter
- Admin-Upload für PDFs
- Cover-Bild Vorschau

Example:
    from v_flask_plugins.katalog import KatalogPlugin

    v_flask = VFlask()
    v_flask.register_plugin(KatalogPlugin())
    v_flask.init_app(app)
"""

from pathlib import Path

from v_flask.plugins import PluginManifest


class KatalogPlugin(PluginManifest):
    """PDF-Blätterkatalog Plugin für v-flask.

    Stellt PDF-Kataloge mit eingebettetem Viewer und Download-Option
    bereit. Kataloge werden nach Kategorien (Hauptkatalog, Neuheiten, etc.)
    organisiert.
    """

    name = 'katalog'
    version = '0.1.0'
    description = 'PDF-Blätterkatalog mit Viewer und Download-Funktion'
    author = 'v-flask'

    # Metadata
    categories = ['content', 'catalog', 'public']
    tags = ['pdf', 'katalog', 'viewer', 'download', 'blätterkatalog']
    admin_category = 'content'

    # UI Slots
    ui_slots = {
        'navbar_items': [
            {
                'label': 'Kataloge',
                'url': 'katalog.index',
                'icon': 'ti ti-book',
                'order': 40,
            }
        ],
        'footer_links': [
            {
                'label': 'PDF-Kataloge',
                'url': 'katalog.index',
                'icon': 'ti ti-book-2',
                'order': 40,
            }
        ],
        'admin_menu': [
            {
                'label': 'Kataloge',
                'url': 'katalog_admin.list_pdfs',
                'icon': 'ti ti-files',
                'permission': 'admin.*',
                'order': 25,
            }
        ],
        'admin_dashboard_widgets': [
            {
                'name': 'PDF-Kataloge',
                'description': 'Kataloge verwalten',
                'url': 'katalog_admin.list_pdfs',
                'icon': 'ti-book',
                'color_hex': '#3b82f6',
            }
        ],
    }

    def get_models(self) -> list[type]:
        """Return SQLAlchemy models for this plugin."""
        from v_flask_plugins.katalog.models import KatalogKategorie, KatalogPDF
        return [KatalogKategorie, KatalogPDF]

    def get_blueprints(self) -> list[tuple]:
        """Return Flask blueprints with URL prefixes."""
        from v_flask_plugins.katalog.routes import katalog_bp, katalog_admin_bp
        return [
            (katalog_bp, '/katalog'),
            (katalog_admin_bp, '/admin/katalog'),
        ]

    def get_template_folder(self) -> Path:
        """Return path to plugin templates."""
        return Path(__file__).parent / 'templates'

    def get_settings_schema(self) -> list[dict]:
        """Define plugin settings."""
        return [
            {
                'key': 'upload_path',
                'label': 'Upload-Pfad',
                'type': 'string',
                'description': 'Relativer Pfad für PDF-Uploads (ab instance/)',
                'default': 'katalog/pdfs',
            },
            {
                'key': 'max_file_size_mb',
                'label': 'Max. Dateigröße (MB)',
                'type': 'int',
                'description': 'Maximale Dateigröße für PDF-Uploads',
                'default': 50,
            },
            {
                'key': 'require_login',
                'label': 'Login für Download erforderlich',
                'type': 'bool',
                'description': 'PDF-Download nur für eingeloggte Benutzer',
                'default': False,
            },
            {
                'key': 'show_view_count',
                'label': 'Ansichten anzeigen',
                'type': 'bool',
                'description': 'View-Counter auf der Katalog-Seite anzeigen',
                'default': False,
            },
            {
                'key': 'show_download_count',
                'label': 'Downloads anzeigen',
                'type': 'bool',
                'description': 'Download-Counter auf der Katalog-Seite anzeigen',
                'default': False,
            },
        ]

    def on_init(self, app) -> None:
        """Called when plugin is initialized."""
        from v_flask_plugins.katalog.services import PDFService

        # Register PDF service in app extensions
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['katalog_pdf_service'] = PDFService(app)

        app.logger.info(f"Katalog plugin v{self.version} initialized")


# Export
__all__ = ['KatalogPlugin']
