"""Content Plugin - Template-based content system for page sections.

This plugin provides a template-based content system for general page areas,
called "Inhaltsbausteine" (content blocks) for end users.

Features:
- Intention-based content creation (Über uns, Leistungen, Team, etc.)
- Multiple layout templates (Banner + Text, Bild links/rechts, etc.)
- Integration with media library for images
- Reusable text snippets with industry-specific templates
- Flexible page assignment via content slots
"""
from pathlib import Path
from v_flask.plugins import PluginManifest


class ContentPlugin(PluginManifest):
    """Plugin for template-based content blocks."""

    # Required metadata
    name = 'content'
    version = '1.0.0'
    description = 'Template-basierte Inhaltsbausteine für Seitenbereiche'
    long_description = '''
Ein template-basiertes Content-System für allgemeine Seitenbereiche.

Features:
- Intentions-basierte Erstellung (Über uns, Leistungen, Team, etc.)
- Mehrere Layout-Templates (Banner + Text, Bild links/rechts, etc.)
- Integration mit der Medienbibliothek
- Wiederverwendbare Textbausteine mit Branchen-Templates
- Flexible Seitenzuweisung via Content-Slots
'''
    author = 'v-flask'

    # Marketplace metadata
    license = 'MIT'
    categories = ['content', 'pages']
    tags = ['bausteine', 'content', 'templates', 'textbausteine']
    min_v_flask_version = '1.0.0'

    # Dependencies
    dependencies = ['media']  # Requires media plugin for image handling

    # Admin navigation
    admin_category = 'content'

    # UI slots for automatic integration
    ui_slots = {
        'admin_menu': [
            {
                'label': 'Inhaltsbausteine',
                'url': 'content_admin.list_blocks',
                'icon': 'ti ti-layout-grid',
                'permission': 'admin.*',
                'order': 20,
            }
        ],
        'admin_dashboard_widgets': [
            {
                'name': 'Inhaltsbausteine',
                'description': 'Content-Bausteine verwalten',
                'url': 'content_admin.list_blocks',
                'icon': 'ti-layout-grid',
                'color_hex': '#8b5cf6',
            }
        ],
    }

    def get_models(self):
        """Return SQLAlchemy models (lazy import!)."""
        from .models import ContentBlock, ContentAssignment, TextSnippet
        return [ContentBlock, ContentAssignment, TextSnippet]

    def get_blueprints(self):
        """Return blueprints with URL prefixes (lazy import!)."""
        from .routes import content_admin_bp
        return [
            (content_admin_bp, '/admin/content'),
        ]

    def get_template_folder(self):
        """Return template directory."""
        return Path(__file__).parent / 'templates'

    def on_init(self, app):
        """Called on app startup - register slot provider."""
        # Register content slot provider
        from v_flask import content_slot_registry
        from v_flask_plugins.content.slot_provider import content_slot_provider
        content_slot_registry.register(content_slot_provider)

        app.logger.info(f'Plugin {self.name} v{self.version} initialized')

    def get_settings_schema(self) -> list[dict]:
        """Define configurable settings."""
        return [
            {
                'key': 'default_layout',
                'label': 'Standard-Layout',
                'type': 'select',
                'options': [
                    {'value': 'banner_text', 'label': 'Banner + Text'},
                    {'value': 'bild_links', 'label': 'Bild links'},
                    {'value': 'bild_rechts', 'label': 'Bild rechts'},
                    {'value': 'nur_text', 'label': 'Nur Text'},
                ],
                'default': 'bild_links',
                'description': 'Standard-Layout für neue Inhaltsbausteine',
            },
            {
                'key': 'enable_snippets',
                'label': 'Textbausteine aktivieren',
                'type': 'bool',
                'default': True,
                'description': 'Vordefinierte Textbausteine zur Auswahl anbieten',
            },
        ]
