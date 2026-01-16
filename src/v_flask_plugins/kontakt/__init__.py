"""Kontakt Plugin for v-flask.

A simple contact form plugin with:
- Public contact form
- Admin interface for viewing submissions
- Read/unread status tracking

Usage:
    from v_flask import VFlask
    from v_flask_plugins.kontakt import KontaktPlugin

    v_flask = VFlask()
    v_flask.register_plugin(KontaktPlugin())
    v_flask.init_app(app)
"""

from pathlib import Path

from v_flask.plugins import PluginManifest


class KontaktPlugin(PluginManifest):
    """Contact form plugin for v-flask applications.

    Provides:
        - Public contact form at /kontakt
        - Admin interface at /admin/kontakt
        - KontaktAnfrage model for storing submissions
    """

    name = 'kontakt'
    version = '1.1.0'  # Added UI slots support
    description = 'Kontaktformular mit Admin-Bereich für Anfragen-Verwaltung'
    author = 'v-flask'

    # No dependencies on other plugins
    dependencies = []

    # Marketplace metadata
    long_description = '''
Ein vollständiges Kontaktformular-Plugin für v-flask Anwendungen.

**Features:**
- Öffentliches Kontaktformular mit Server-seitiger Validierung
- Admin-Bereich zum Verwalten von Anfragen
- Lese-Status-Tracking (gelesen/ungelesen)
- Responsive Templates basierend auf DaisyUI

Das Plugin funktioniert standalone ohne externe Abhängigkeiten.
'''
    license = 'MIT'
    categories = ['forms', 'communication']
    tags = ['kontakt', 'formular', 'contact', 'admin', 'anfrage', 'email']
    min_v_flask_version = '0.2.0'  # Requires UI slots feature

    # Admin navigation: appears under "Kommunikation" category
    admin_category = 'communication'

    # UI Slots: Automatic UI integration when plugin is activated
    ui_slots = {
        'footer_links': [
            {
                'label': 'Kontakt',
                'url': 'kontakt.form',
                'icon': 'ti ti-mail',
                'order': 100,
            }
        ],
        'admin_menu': [
            {
                'label': 'Kontakt-Anfragen',
                'url': 'kontakt_admin.list_anfragen',
                'icon': 'ti ti-inbox',
                'badge_func': 'get_unread_count',
                'permission': 'admin.*',
                'order': 10,  # First in communication category
            }
        ],
        'admin_dashboard_widgets': [
            {
                'name': 'Kontakt-Anfragen',
                'description': 'Ungelesene Nachrichten verwalten',
                'icon': 'ti-inbox',
                'url': 'kontakt_admin.list_anfragen',
                'badge_func': 'get_unread_count',
                'color_hex': '#10b981',
                'order': 100,
            }
        ],
    }

    def get_unread_count(self) -> int:
        """Get count of unread contact submissions.

        Used by ui_slots badge_func to display unread count in admin UI.
        """
        try:
            from v_flask.extensions import db
            from v_flask_plugins.kontakt.models import KontaktAnfrage
            return db.session.query(KontaktAnfrage).filter_by(gelesen=False).count()
        except Exception:
            return 0

    def get_models(self):
        """Return the KontaktAnfrage model."""
        from v_flask_plugins.kontakt.models import KontaktAnfrage
        return [KontaktAnfrage]

    def get_blueprints(self):
        """Return public and admin blueprints."""
        from v_flask_plugins.kontakt.routes import kontakt_bp, kontakt_admin_bp
        return [
            (kontakt_bp, '/kontakt'),
            (kontakt_admin_bp, '/admin/kontakt'),
        ]

    def get_template_folder(self):
        """Return path to plugin templates."""
        return Path(__file__).parent / 'templates'

    def on_init(self, app):
        """Register nl2br Jinja filter if not already available."""
        from markupsafe import Markup

        if 'nl2br' not in app.jinja_env.filters:
            @app.template_filter('nl2br')
            def nl2br_filter(text):
                """Convert newlines to <br> tags."""
                if not text:
                    return ''
                return Markup(str(text).replace('\n', '<br>\n'))


# Export the plugin class
__all__ = ['KontaktPlugin']
