"""Datenschutz Plugin for v-flask.

Generates a DSGVO-compliant privacy policy (Datenschutzerklärung) with:
- Automatic detection of used services (plugins, templates)
- Pre-written legally compliant text modules (Bausteine)
- Admin editor with service selection and live preview
- Version history for compliance audits

Usage:
    from v_flask import VFlask
    from v_flask_plugins.datenschutz import DatenschutzPlugin

    v_flask = VFlask()
    v_flask.register_plugin(DatenschutzPlugin())
    v_flask.init_app(app)
"""

from pathlib import Path

from v_flask.plugins import PluginManifest


class DatenschutzPlugin(PluginManifest):
    """DSGVO-compliant privacy policy generator plugin for v-flask.

    Provides:
        - Public privacy policy page at /datenschutz
        - Admin editor at /admin/datenschutz with live preview
        - Automatic detection of services from plugins and templates
        - Pre-written text modules (Bausteine) for common services
        - Version history for compliance tracking
    """

    name = 'datenschutz'
    version = '1.0.0'
    description = 'DSGVO-konforme Datenschutzerklärung mit automatischer Diensterkennung'
    author = 'v-flask'

    # Dependencies: requires impressum for Betreiber data import
    dependencies = []

    # Marketplace metadata
    long_description = '''
Ein Plugin zur Erstellung einer DSGVO-konformen Datenschutzerklärung.

**Features:**
- Automatische Erkennung verwendeter Dienste (Plugins, eingebundene Scripts)
- Vorgefertigte rechtssichere Textbausteine
- "Aus Impressum übernehmen"-Funktion für Verantwortlicher-Daten
- Live-Vorschau im Admin-Editor
- Versionierung für Compliance-Audits
- Warnungen bei erkannten aber nicht konfigurierten Diensten

**Pflichtangaben nach DSGVO Art. 13/14:**
- Verantwortlicher (Name, Anschrift, Kontakt)
- Datenschutzbeauftragter (falls vorhanden)
- Betroffenenrechte (Auskunft, Löschung, Widerspruch)
- Beschwerderecht bei Aufsichtsbehörde
- Verarbeitungszwecke und Rechtsgrundlagen

**Vordefinierte Bausteine:**
- Server-Logs, SSL, Cookies
- Kontaktformular, E-Mail
- Google Analytics, Matomo
- YouTube, Google Maps, Social Media
- Newsletter, Zahlungsanbieter
'''
    license = 'MIT'
    categories = ['legal', 'compliance', 'privacy']
    tags = ['datenschutz', 'dsgvo', 'gdpr', 'privacy', 'recht', 'germany']
    min_v_flask_version = '0.1.0'

    # Admin navigation: appears under "Rechtliches" category
    admin_category = 'legal'

    # UI Slots: Automatic UI integration when plugin is activated
    ui_slots = {
        'footer_links': [
            {
                'label': 'Datenschutz',
                'url': 'datenschutz.public',
                'icon': 'ti ti-shield-lock',
                'order': 210,  # After Impressum (200)
            }
        ],
        'admin_menu': [
            {
                'label': 'Datenschutz',
                'url': 'datenschutz_admin.editor',
                'icon': 'ti ti-shield-lock',
                'permission': 'admin.*',
                'order': 20,  # Second in legal category
            }
        ],
    }

    def get_models(self):
        """Return models used by this plugin."""
        from v_flask_plugins.datenschutz.models import (
            DatenschutzConfig,
            DatenschutzVersion,
        )
        return [DatenschutzConfig, DatenschutzVersion]

    def get_blueprints(self):
        """Return public and admin blueprints."""
        from v_flask_plugins.datenschutz.routes import (
            datenschutz_admin_bp,
            datenschutz_bp,
        )
        return [
            (datenschutz_bp, '/datenschutz'),
            (datenschutz_admin_bp, '/admin/datenschutz'),
        ]

    def get_template_folder(self):
        """Return path to plugin templates."""
        return Path(__file__).parent / 'templates'

    def get_help_texts(self):
        """Return help texts for the Datenschutz editor."""
        return [{
            'schluessel': 'datenschutz.editor',
            'titel': 'Hilfe zur Datenschutzerklärung',
            'inhalt_markdown': '''## Warum eine Datenschutzerklärung?

Nach **Art. 13 und 14 DSGVO** müssen Sie Nutzer über die Verarbeitung ihrer
personenbezogenen Daten informieren. Eine fehlende oder unvollständige
Datenschutzerklärung kann zu **Bußgeldern** führen.

## Pflichtangaben

Folgende Angaben sind gesetzlich vorgeschrieben:

- **Verantwortlicher** (Name, Anschrift, Kontakt)
- **Datenschutzbeauftragter** (falls vorhanden/erforderlich)
- **Verarbeitungszwecke** und Rechtsgrundlagen
- **Betroffenenrechte** (Auskunft, Löschung, Widerspruch)
- **Beschwerderecht** bei der Aufsichtsbehörde

## Bausteine

Die Bausteine decken typische Verarbeitungsvorgänge ab:

- **Pflichtbausteine** sind automatisch aktiviert und können nicht deaktiviert werden
- **Optionale Bausteine** aktivieren Sie je nach verwendeten Diensten
- Das System erkennt einige Dienste automatisch

## Automatische Erkennung

Das System prüft Ihre Website auf eingebundene Dienste (z.B. Google Analytics,
YouTube-Videos) und zeigt Warnungen, wenn diese noch nicht konfiguriert sind.

## Disclaimer

**Wichtig:** Dieses Tool unterstützt Sie bei der Erstellung einer
Datenschutzerklärung, **ersetzt jedoch keine Rechtsberatung**. Für die
rechtliche Korrektheit und Vollständigkeit übernehmen wir keine Haftung.

Bei Unsicherheiten empfehlen wir die Prüfung durch einen
**Datenschutzbeauftragten oder Rechtsanwalt**.
'''
        }]

    def on_init(self, app):
        """Initialize plugin-specific functionality.

        Registers template context processors for Datenschutz helpers.
        """
        @app.context_processor
        def datenschutz_context():
            """Provide Datenschutz helpers in templates."""
            def get_datenschutz_html():
                """Generate HTML Datenschutzerklärung from current config."""
                try:
                    from v_flask.extensions import db
                    from v_flask_plugins.datenschutz.generator import (
                        DatenschutzGenerator,
                    )
                    from v_flask_plugins.datenschutz.models import DatenschutzConfig

                    config = db.session.query(DatenschutzConfig).first()
                    if config:
                        generator = DatenschutzGenerator(config)
                        return generator.generate_html()
                except Exception:
                    pass
                return ''

            def get_detected_services():
                """Get list of automatically detected services."""
                try:
                    from flask import current_app

                    from v_flask_plugins.datenschutz.detector import DienstErkennung

                    detector = DienstErkennung(current_app)
                    return detector.detect_all()
                except Exception:
                    pass
                return []

            return {
                'get_datenschutz_html': get_datenschutz_html,
                'get_detected_services': get_detected_services,
            }


# Export the plugin class
__all__ = ['DatenschutzPlugin']
