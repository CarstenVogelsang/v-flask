"""Fragebogen (Questionnaire) Plugin for v-flask.

A complete questionnaire system with:
- Multi-page wizard questionnaires (V2 schema)
- Magic-Link access for known participants
- Anonymous participation with contact data collection
- Conditional logic (show_if)
- Prefill from participant data
- Admin dashboard with statistics
- XLSX export

Usage:
    from v_flask import VFlask
    from v_flask_plugins.fragebogen import FragebogenPlugin

    v_flask = VFlask()
    v_flask.register_plugin(FragebogenPlugin())
    v_flask.init_app(app)
"""

from pathlib import Path

from v_flask.plugins import PluginManifest


class FragebogenPlugin(PluginManifest):
    """Questionnaire plugin for v-flask applications.

    Provides:
        - Multi-page wizard questionnaires
        - Magic-Link system for login-free participation
        - Anonymous participation with contact data
        - Conditional question display (show_if)
        - Prefill fields from participant data
        - Auto-save during wizard
        - Admin dashboard with statistics
        - XLSX export
        - Questionnaire versioning
    """

    name = 'fragebogen'
    version = '1.0.0'
    description = 'Mehrseitige Wizard-Fragebögen mit Magic-Link System'
    author = 'v-flask'

    # No dependencies on other plugins
    dependencies = []

    # Marketplace metadata
    long_description = '''
Ein vollständiges Fragebogen-System für v-flask Anwendungen.

**Features:**
- Mehrseitige Wizard-Fragebögen (V2 Schema)
- Magic-Link für Login-freie Teilnahme
- Anonyme Teilnahme mit Kontaktdatenerfassung
- Bedingte Anzeige von Fragen (show_if)
- Vorausfüllung aus Teilnehmerdaten (prefill)
- Auto-Save während des Ausfüllens
- Admin-Dashboard mit Statistiken
- XLSX-Export der Antworten
- Versionierung von Fragebögen

**Fragetypen:**
- single_choice: Radio Buttons
- multiple_choice: Checkboxen
- dropdown: Dropdown mit Freifeld-Option
- skala: Bewertungsskala
- text: Freitext/Textarea
- ja_nein: Ja/Nein Buttons
- date: Datumseingabe
- number: Zahleneingabe
- url: URL-Validierung
- group: Feldgruppe
- table: Matrix-Fragen

**Teilnehmer-System:**
- Flexibler Foreign-Key (teilnehmer_id + teilnehmer_typ)
- Unterstützt Kunden, Benutzer, Leads, etc.
- Magic-Link Token für direkten Zugang
- Anonyme Teilnahme mit Kontaktdatenerfassung
'''
    license = 'MIT'
    categories = ['forms', 'surveys']
    tags = ['fragebogen', 'umfrage', 'wizard', 'magic-link', 'survey', 'questionnaire']
    min_v_flask_version = '0.2.0'

    # Admin navigation: appears under "Inhalte" category
    admin_category = 'content'

    # UI Slots: Automatic UI integration when plugin is activated
    ui_slots = {
        'admin_menu': [
            {
                'label': 'Fragebögen',
                'url': 'fragebogen_admin.index',
                'icon': 'ti ti-clipboard-list',
                'badge_func': 'get_active_count',
                'permission': 'admin.*',
                'order': 30,
            }
        ],
        'admin_dashboard_widgets': [
            {
                'name': 'Fragebögen',
                'description': 'Aktive Fragebögen verwalten',
                'icon': 'ti-clipboard-list',
                'url': 'fragebogen_admin.index',
                'badge_func': 'get_active_count',
                'color_hex': '#10b981',
                'order': 60,
            }
        ],
    }

    def get_active_count(self) -> int:
        """Get count of active questionnaires.

        Used by ui_slots badge_func to display count in admin UI.
        """
        try:
            from v_flask.extensions import db
            from v_flask_plugins.fragebogen.models import Fragebogen
            return db.session.query(Fragebogen).filter_by(
                status='aktiv',
                archiviert=False
            ).count()
        except Exception:
            return 0

    def get_models(self):
        """Return all plugin models."""
        from v_flask_plugins.fragebogen.models import (
            Fragebogen,
            FragebogenTeilnahme,
            FragebogenAntwort,
        )
        return [Fragebogen, FragebogenTeilnahme, FragebogenAntwort]

    def get_blueprints(self):
        """Return admin and public blueprints."""
        from v_flask_plugins.fragebogen.routes import admin_bp, public_bp
        return [
            (admin_bp, '/admin/fragebogen'),
            (public_bp, '/fragebogen'),
        ]

    def get_template_folder(self):
        """Return path to plugin templates."""
        return Path(__file__).parent / 'templates'

    def get_static_folder(self):
        """Return path to plugin static files."""
        static_folder = Path(__file__).parent / 'static'
        if static_folder.exists():
            return static_folder
        return None

    def on_init(self, app):
        """Initialize plugin."""
        pass

    def get_help_texts(self):
        """Return help texts for the plugin."""
        return [
            {
                'schluessel': 'fragebogen.wizard',
                'titel': 'Fragebogen ausfüllen',
                'inhalt_markdown': '''## Fragebogen ausfüllen

Der Fragebogen führt Sie Schritt für Schritt durch alle Fragen.

### Navigation
- **Weiter**: Zur nächsten Seite
- **Zurück**: Zur vorherigen Seite
- **Abschließen**: Fragebogen einreichen

### Auto-Save
Ihre Antworten werden automatisch gespeichert. Sie können den
Fragebogen jederzeit unterbrechen und später fortsetzen.

### Pflichtfelder
Felder mit * müssen ausgefüllt werden, bevor Sie fortfahren können.
''',
            },
            {
                'schluessel': 'fragebogen.admin.erstellen',
                'titel': 'Fragebogen erstellen',
                'inhalt_markdown': '''## Fragebogen erstellen

### Status-Workflow
1. **Entwurf**: Fragebogen wird bearbeitet
2. **Aktiv**: Teilnehmer können ausfüllen
3. **Geschlossen**: Keine neuen Antworten

### Fragetypen
- **Text**: Freitext-Eingabe
- **Single Choice**: Eine Option wählen
- **Multiple Choice**: Mehrere Optionen
- **Skala**: Bewertungsskala (1-5, 1-10, etc.)
- **Ja/Nein**: Einfache Ja/Nein-Frage

### Bedingte Anzeige
Mit `show_if` können Fragen basierend auf vorherigen Antworten
ein- oder ausgeblendet werden.
''',
            },
        ]


# Export the plugin class
__all__ = ['FragebogenPlugin']
