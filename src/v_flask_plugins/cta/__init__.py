"""CTA (Call-to-Action) Plugin for v-flask.

A Call-to-Action plugin that provides:
- Dynamic CTA sections with Jinja2 placeholders
- Three design variants: Card, Alert, Floating
- Route-based slot assignment (like Hero)
- Admin interface with live preview

Usage:
    from v_flask import VFlask
    from v_flask_plugins.cta import CtaPlugin

    v_flask = VFlask()
    v_flask.register_plugin(CtaPlugin())
    v_flask.init_app(app)

In templates:
    {{ render_content_slot('after_content', context={'ort': ort}) }}
"""

from pathlib import Path

from v_flask.plugins import PluginManifest


class CtaPlugin(PluginManifest):
    """CTA (Call-to-Action) plugin for v-flask applications.

    Provides:
        - CTA sections with 3 design variants
        - Text templates with Jinja2 placeholders
        - Route-based slot assignment
        - Admin editor with live preview
    """

    name = 'cta'
    version = '1.0.0'
    description = 'Call-to-Action Sections mit 3 Design-Varianten (Card, Alert, Floating)'
    author = 'v-flask'

    # Optional dependency on hero (for shared PageRoute)
    dependencies = []

    # Marketplace metadata
    long_description = '''
Ein flexibles CTA (Call-to-Action) Plugin für v-flask Anwendungen.

**Features:**
- Drei Design-Varianten: Card, Alert, Floating
- Text-Vorlagen mit Jinja2-Platzhaltern ({{ plattform.name }}, {{ ort.name }})
- Route-basierte Seitenzuweisung
- Live-Vorschau im Admin-Editor
- Prioritätssteuerung bei mehreren CTAs

**Verfügbare Platzhalter:**
- `{{ plattform.name }}` - Plattformname
- `{{ plattform.zielgruppe }}` - Zielgruppe
- `{{ location.bezeichnung }}` - Bezeichnung für Locations
- `{{ ort.name }}` - Ortsname (aus Template-Kontext)
- `{{ kreis.name }}` - Kreisname (aus Template-Kontext)
- `{{ bundesland.name }}` - Bundeslandname (aus Template-Kontext)

**Verwendung im Template:**
```jinja2
{{ render_content_slot('after_content', context={'ort': ort}) }}
```
'''
    license = 'MIT'
    categories = ['content', 'marketing']
    tags = ['cta', 'call-to-action', 'marketing', 'conversion', 'banner']
    min_v_flask_version = '0.2.0'

    # Admin navigation: appears under "Inhalte" category
    admin_category = 'content'

    # UI Slots: Automatic UI integration when plugin is activated
    ui_slots = {
        'admin_menu': [
            {
                'label': 'CTA Sections',
                'url': 'cta_admin.list_sections',
                'icon': 'ti ti-click',
                'permission': 'admin.*',
                'order': 10,  # After Hero
            }
        ],
    }

    def get_models(self):
        """Return all CTA plugin models."""
        from v_flask_plugins.cta.models import CtaTemplate, CtaSection, CtaAssignment
        return [CtaTemplate, CtaSection, CtaAssignment]

    def get_blueprints(self):
        """Return admin blueprint for CTA configuration."""
        from v_flask_plugins.cta.routes import cta_admin_bp
        return [
            (cta_admin_bp, '/admin/cta'),
        ]

    def get_template_folder(self):
        """Return path to plugin templates."""
        return Path(__file__).parent / 'templates'

    def get_settings_schema(self) -> list[dict]:
        """Define available settings for the CTA plugin.

        Returns:
            List of setting definitions for layout and behavior options.
        """
        return [
            {
                'key': 'default_variant',
                'label': 'Standard-Design',
                'type': 'select',
                'description': 'Design-Variante für neue CTA Sections',
                'options': [
                    {'value': 'card', 'label': 'Card'},
                    {'value': 'alert', 'label': 'Alert'},
                    {'value': 'floating', 'label': 'Floating'},
                ],
                'default': 'card',
            },
            {
                'key': 'plattform_name',
                'label': 'Plattform-Name',
                'type': 'string',
                'description': 'Name der Plattform für Platzhalter {{ plattform.name }}',
                'default': '',
                'help': 'Leer = Betreibername aus Einstellungen',
            },
            {
                'key': 'plattform_zielgruppe',
                'label': 'Zielgruppe',
                'type': 'string',
                'description': 'Zielgruppe für Platzhalter {{ plattform.zielgruppe }}',
                'default': 'Café, Restaurant oder Hotel',
            },
            {
                'key': 'location_bezeichnung',
                'label': 'Location-Bezeichnung',
                'type': 'string',
                'description': 'Bezeichnung für Locations {{ location.bezeichnung }}',
                'default': 'Lokal',
            },
            {
                'key': 'excluded_blueprints',
                'label': 'Ausgeschlossene Blueprints',
                'type': 'textarea',
                'description': 'Ein Blueprint pro Zeile. Diese werden bei der Seitenzuweisung nicht angezeigt.',
                'default': 'admin\nanbieter\nmein_bereich\nmedia\nmedia_admin\ntwo_fa\nauth',
            },
        ]

    def on_init(self, app):
        """Register content slot provider."""
        # Register CTA as a content slot provider
        try:
            from v_flask import content_slot_registry
            from v_flask_plugins.cta.slot_provider import cta_slot_provider

            content_slot_registry.register(cta_slot_provider)
            app.logger.debug('CTA plugin registered as content slot provider')
        except (ImportError, ValueError) as e:
            # ImportError: content_slots not available
            # ValueError: Already registered
            app.logger.debug(f'CTA slot provider registration skipped: {e}')


# Export the plugin class
__all__ = ['CtaPlugin']
