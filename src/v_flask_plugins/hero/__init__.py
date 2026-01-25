"""Hero Section Plugin for v-flask.

A hero section plugin with multiple layout variants:
- Centered: Text centered over image
- Split: Image left, text right
- Overlay: Full-screen with dark gradient overlay

Features:
- Three layout variants
- Text templates with Jinja2 placeholders
- Media Library integration (via media plugin)
- CTA button configuration
- Live preview in admin

Usage:
    from v_flask import VFlask
    from v_flask_plugins.hero import HeroPlugin

    v_flask = VFlask()
    v_flask.register_plugin(HeroPlugin())
    v_flask.init_app(app)

In templates:
    {{ render_hero_section() }}

Dependencies:
    - media: Required for image management
"""

from pathlib import Path

from v_flask.plugins import PluginManifest


class HeroPlugin(PluginManifest):
    """Hero Section plugin for v-flask applications.

    Provides:
        - Hero section with 3 layout variants
        - Text templates with placeholders
        - Admin editor with live preview
        - Frontend rendering via context processor
    """

    name = 'hero'
    version = '1.0.0'
    description = 'Hero Section mit 3 Layout-Varianten (Zentriert, Geteilt, Overlay)'
    author = 'v-flask'

    # Requires media plugin for image management
    dependencies = ['media']

    # Marketplace metadata
    long_description = '''
Ein flexibles Hero Section Plugin für v-flask Anwendungen.

**Features:**
- Drei Layout-Varianten: Zentriert, Geteilt, Overlay
- Text-Vorlagen mit Jinja2-Platzhaltern ({{ betreiber.name }})
- Integration mit Media-Bibliothek für Hintergründe
- Call-to-Action Button
- Live-Vorschau im Admin-Editor
- HTMX-basierte interaktive Bearbeitung

**Verwendung im Template:**
```jinja2
{{ render_hero_section() }}
```

**Abhängigkeit:** Benötigt das `media` Plugin für Bildverwaltung.
'''
    license = 'MIT'
    categories = ['content', 'design']
    tags = ['hero', 'header', 'landing', 'banner', 'section', 'layout']
    min_v_flask_version = '0.2.0'

    # Admin navigation: appears under "Inhalte" category
    admin_category = 'content'

    # UI Slots: Automatic UI integration when plugin is activated
    ui_slots = {
        'admin_menu': [
            {
                'label': 'Hero Sections',
                'url': 'hero_admin.list_sections',
                'icon': 'ti ti-photo',
                'permission': 'admin.*',
                'order': 5,  # Early in content category
            }
        ],
    }

    def get_models(self):
        """Return all Hero plugin models.

        Note: PageRoute is now defined in v_flask.content_slots.models (Core).
        It's re-exported from hero.models for backwards compatibility.
        We don't include it here as it's registered by v-flask Core.
        """
        from v_flask_plugins.hero.models import (
            HeroSection,
            HeroTemplate,
            HeroAssignment,
        )
        return [HeroSection, HeroTemplate, HeroAssignment]

    def get_blueprints(self):
        """Return admin blueprint for hero configuration."""
        from v_flask_plugins.hero.routes import hero_admin_bp
        return [
            (hero_admin_bp, '/admin/hero'),
        ]

    def get_template_folder(self):
        """Return path to plugin templates."""
        return Path(__file__).parent / 'templates'

    def get_settings_schema(self) -> list[dict]:
        """Define available settings for the Hero plugin.

        Returns:
            List of setting definitions for layout and behavior options.
        """
        return [
            {
                'key': 'default_variant',
                'label': 'Standard-Layout',
                'type': 'select',
                'description': 'Layout-Variante für neue Hero Sections',
                'options': [
                    {'value': 'centered', 'label': 'Zentriert'},
                    {'value': 'split', 'label': 'Geteilt'},
                    {'value': 'overlay', 'label': 'Overlay'},
                ],
                'default': 'centered',
            },
            {
                'key': 'show_cta_default',
                'label': 'CTA standardmäßig anzeigen',
                'type': 'bool',
                'description': 'Call-to-Action Button in neuen Hero Sections anzeigen',
                'default': True,
            },
            {
                'key': 'min_height',
                'label': 'Mindesthöhe (vh)',
                'type': 'int',
                'description': 'Mindesthöhe der Hero Section in Viewport-Höhe (50-100)',
                'default': 60,
                'min': 50,
                'max': 100,
            },
            {
                'key': 'excluded_blueprints',
                'label': 'Ausgeschlossene Blueprints',
                'type': 'textarea',
                'description': 'Ein Blueprint pro Zeile. Diese werden bei der Seitenzuweisung nicht angezeigt.',
                'default': 'admin\nanbieter\nmein_bereich\nmedia\nmedia_admin\ntwo_fa\nauth',
                'help': 'Blueprints wie "admin", "auth" etc. werden nicht in der Dropdown-Liste für Seitenzuweisungen angezeigt.',
            },
            {
                'key': 'show_only_public',
                'label': 'Nur öffentliche Seiten anzeigen',
                'type': 'bool',
                'description': 'Wenn aktiv, werden nur Seiten vom Typ "page" für Hero-Zuweisungen angezeigt.',
                'default': True,
            },
        ]

    def on_init(self, app):
        """Register context processor and content slot provider."""
        from flask import request
        from v_flask_plugins.hero.services.hero_service import hero_service

        # Register Hero as a content slot provider for the generic slot system
        try:
            from v_flask import content_slot_registry
            from v_flask_plugins.hero.slot_provider import hero_slot_provider

            content_slot_registry.register(hero_slot_provider)
            app.logger.debug('Hero plugin registered as content slot provider')
        except (ImportError, ValueError) as e:
            # ImportError: content_slots not available (older v-flask)
            # ValueError: Already registered (e.g., during hot reload)
            app.logger.debug(f'Hero slot provider registration skipped: {e}')

        @app.context_processor
        def hero_context():
            """Provide hero rendering functions to templates."""

            def render_hero_section():
                """Render the active hero section (legacy).

                Usage in templates:
                    {{ render_hero_section() }}

                Returns:
                    Rendered HTML string or empty string if no hero configured.
                """
                return hero_service.render_active_hero()

            def get_active_hero():
                """Get the active hero section model.

                Usage in templates:
                    {% set hero = get_active_hero() %}
                    {% if hero %}
                        {% include 'hero/' ~ hero.variant ~ '.html' %}
                    {% endif %}

                Returns:
                    HeroSection instance or None.
                """
                return hero_service.get_active_hero()

            def render_hero_slot(slot: str = 'hero_top') -> str:
                """Render hero section for current endpoint and slot.

                New route-based hero rendering. Finds the hero section
                assigned to the current page and specified slot position.

                Usage in templates:
                    {{ render_hero_slot('hero_top') }}
                    {{ render_hero_slot('above_content') }}
                    {{ render_hero_slot('below_content') }}

                Args:
                    slot: Slot position ('hero_top', 'above_content', 'below_content').

                Returns:
                    Rendered HTML string or empty string if no hero assigned.
                """
                if not request.endpoint:
                    return ''
                return hero_service.render_hero_slot(request.endpoint, slot)

            return {
                'render_hero_section': render_hero_section,  # Legacy
                'get_active_hero': get_active_hero,
                'render_hero_slot': render_hero_slot,  # New route-based
            }


# Export the plugin class
__all__ = ['HeroPlugin']
