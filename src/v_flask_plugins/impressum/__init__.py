"""Impressum Plugin for v-flask.

Generates a legally compliant German Impressum (§ 5 TMG) from structured data:
- Auto-generated Impressum text from Betreiber data
- Admin editor with live preview
- Validation with warnings for missing required fields
- Toggle options for optional sections (V.i.S.d.P., Streitschlichtung)

Usage:
    from v_flask import VFlask
    from v_flask_plugins.impressum import ImpressumPlugin

    v_flask = VFlask()
    v_flask.register_plugin(ImpressumPlugin())
    v_flask.init_app(app)
"""

from pathlib import Path

from v_flask.plugins import PluginManifest


class ImpressumPlugin(PluginManifest):
    """German Impressum generator plugin for v-flask applications.

    Provides:
        - Public Impressum page at /impressum
        - Admin editor at /admin/impressum with live preview
        - Validation of required fields (Pflichtangaben)
        - ImpressumGenerator for HTML/text output
    """

    name = 'impressum'
    version = '1.0.0'
    description = 'Gesetzeskonformes deutsches Impressum mit Admin-Editor und Validierung'
    author = 'v-flask'

    # No dependencies on other plugins
    dependencies = []

    # Marketplace metadata
    long_description = '''
Ein Plugin zur Erstellung eines gesetzeskonformen deutschen Impressums nach § 5 TMG.

**Features:**
- Strukturierte Dateneingabe (keine Freitext-Bearbeitung)
- Live-Vorschau im Admin-Editor
- Validierung mit Fehler- und Warnmeldungen
- Toggle-Optionen für optionale Abschnitte (V.i.S.d.P., Streitschlichtung)
- Automatisch generierte öffentliche Impressum-Seite
- Unterstützung für Kapitalgesellschaften (GmbH, UG, AG)

**Pflichtangaben nach § 5 TMG:**
- Name und Anschrift des Diensteanbieters
- Vertretungsberechtigter (bei juristischen Personen)
- E-Mail-Adresse
- Handelsregistereintrag (falls vorhanden)
- USt-IdNr. (falls vorhanden)
'''
    license = 'MIT'
    categories = ['legal', 'compliance']
    tags = ['impressum', 'legal', 'tmg', 'recht', 'pflichtangaben', 'germany']
    min_v_flask_version = '0.1.0'

    # Admin navigation: appears under "Rechtliches" category
    admin_category = 'legal'

    # UI Slots: Automatic UI integration when plugin is activated
    ui_slots = {
        'footer_links': [
            {
                'label': 'Impressum',
                'url': 'impressum.public',
                'icon': 'ti ti-file-certificate',
                'order': 200,  # After Kontakt (100)
            }
        ],
        'admin_menu': [
            {
                'label': 'Impressum',
                'url': 'impressum_admin.editor',
                'icon': 'ti ti-file-certificate',
                'permission': 'admin.*',
                'order': 10,  # First in legal category
            }
        ],
    }

    def get_models(self):
        """Return models used by this plugin.

        Note: This plugin uses the existing Betreiber model
        (extended with Impressum fields) rather than its own model.
        """
        return []

    def get_blueprints(self):
        """Return public and admin blueprints."""
        from v_flask_plugins.impressum.routes import impressum_bp, impressum_admin_bp
        return [
            (impressum_bp, '/impressum'),
            (impressum_admin_bp, '/admin/impressum'),
        ]

    def get_template_folder(self):
        """Return path to plugin templates."""
        return Path(__file__).parent / 'templates'

    def get_help_texts(self):
        """Return help texts for the Impressum editor."""
        return [{
            'schluessel': 'impressum.editor',
            'titel': 'Hilfe zum Impressum',
            'inhalt_markdown': '''## Warum ein Impressum?

Nach **§ 5 TMG** (Telemediengesetz) sind geschäftsmäßige Online-Dienste zur
Angabe eines Impressums verpflichtet. Ein fehlendes oder unvollständiges
Impressum kann zu **Abmahnungen** führen.

## Pflichtangaben

Folgende Angaben sind gesetzlich vorgeschrieben:

- **Name und Anschrift** des Diensteanbieters
- **E-Mail-Adresse** für schnelle Kontaktaufnahme
- Bei juristischen Personen (GmbH, UG, AG):
  - **Vertretungsberechtigte** (Geschäftsführer)
  - **Handelsregister** mit Registergericht und -nummer
- **USt-IdNr.** (falls vorhanden)

## Optionale Angaben

- **V.i.S.d.P.** - Für redaktionell-journalistische Inhalte nach § 55 Abs. 2 RStV
- **Streitschlichtung** - Hinweis auf EU-Schlichtungsplattform

## Disclaimer

**Wichtig:** Dieses Tool unterstützt Sie bei der Erstellung eines
Impressums, **ersetzt jedoch keine Rechtsberatung**. Für die rechtliche
Korrektheit und Vollständigkeit des Impressums übernehmen wir keine Haftung.

Bei Unsicherheiten empfehlen wir die Prüfung durch einen **Rechtsanwalt**.
'''
        }]

    def on_init(self, app):
        """Initialize plugin-specific functionality.

        Registers template context processors for Impressum helpers.
        """
        @app.context_processor
        def impressum_context():
            """Provide Impressum helpers in templates."""
            def get_impressum_html():
                """Generate HTML Impressum from current Betreiber."""
                try:
                    from v_flask.extensions import db
                    from v_flask.models import Betreiber
                    from v_flask_plugins.impressum.generator import ImpressumGenerator

                    betreiber = db.session.query(Betreiber).first()
                    if betreiber:
                        generator = ImpressumGenerator(betreiber)
                        return generator.generate_html()
                except Exception:
                    pass
                return ''

            def get_impressum_validation():
                """Get validation result for current Betreiber."""
                try:
                    from v_flask.extensions import db
                    from v_flask.models import Betreiber
                    from v_flask_plugins.impressum.validators import ImpressumValidator

                    betreiber = db.session.query(Betreiber).first()
                    if betreiber:
                        validator = ImpressumValidator(betreiber)
                        return validator.validate()
                except Exception:
                    pass
                return None

            return {
                'get_impressum_html': get_impressum_html,
                'get_impressum_validation': get_impressum_validation,
            }


# Export the plugin class
__all__ = ['ImpressumPlugin']
