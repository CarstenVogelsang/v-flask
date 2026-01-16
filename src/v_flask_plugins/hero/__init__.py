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
                'label': 'Hero Section',
                'url': 'hero_admin.editor',
                'icon': 'ti ti-photo',
                'permission': 'admin.*',
                'order': 5,  # Early in content category
            }
        ],
    }

    def get_models(self):
        """Return HeroSection and HeroTemplate models."""
        from v_flask_plugins.hero.models import HeroSection, HeroTemplate
        return [HeroSection, HeroTemplate]

    def get_blueprints(self):
        """Return admin blueprint for hero configuration."""
        from v_flask_plugins.hero.routes import hero_admin_bp
        return [
            (hero_admin_bp, '/admin/hero'),
        ]

    def get_template_folder(self):
        """Return path to plugin templates."""
        return Path(__file__).parent / 'templates'

    def on_init(self, app):
        """Register context processor for hero rendering."""
        from v_flask_plugins.hero.services.hero_service import hero_service

        @app.context_processor
        def hero_context():
            """Provide render_hero_section() function to templates."""
            def render_hero_section():
                """Render the active hero section.

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

            return {
                'render_hero_section': render_hero_section,
                'get_active_hero': get_active_hero,
            }


# Export the plugin class
__all__ = ['HeroPlugin']
